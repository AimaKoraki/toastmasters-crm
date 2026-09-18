from fastapi import APIRouter, Request, Form, Depends, HTTPException, status as http_status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import supabase
from app.dependencies import get_current_user, require_admin
from app.utils.security import hash_password, verify_password, validate_password_strength
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

USER_ROLES = ["Admin", "Exco", "Viewer"]


_MOCK_USERS = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@apiitkandy.club",
        "full_name": "System Administrator",
        "role": "Admin",
        "member_id": None,
        "is_active": True,
        "must_change_password": False,
        "last_login": None,
        "created_at": "2026-09-01T00:00:00Z",
        "members": None
    }
]


def fetch_users_data(role_filter: str = "all", search_query: str = "") -> list:
    """Helper to query users from Supabase with member relations."""
    if not supabase:
        users = list(_MOCK_USERS)
        if role_filter and role_filter != "all":
            users = [u for u in users if u.get("role") == role_filter]
        if search_query:
            sq = search_query.lower().strip()
            users = [
                u for u in users
                if sq in u.get("full_name", "").lower()
                or sq in u.get("username", "").lower()
                or sq in u.get("email", "").lower()
            ]
        return users

    try:
        query = supabase.table("users").select(
            "id, username, email, full_name, role, member_id, is_active, must_change_password, last_login, created_at, members(id, full_name, email)"
        ).order("created_at", desc=True)

        if role_filter and role_filter != "all":
            query = query.eq("role", role_filter)

        res = query.execute()
        users = res.data or []

        if search_query:
            sq = search_query.lower().strip()
            users = [
                u for u in users
                if sq in u.get("full_name", "").lower()
                or sq in u.get("username", "").lower()
                or sq in u.get("email", "").lower()
            ]

        return users
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []


def get_available_members(exclude_user_id: int = None) -> list:
    """Fetches club members that are not already linked to another user account (1-to-1)."""
    if not supabase:
        return []

    try:
        members_res = supabase.table("members").select("id, full_name, email").order("full_name").execute()
        all_members = members_res.data or []

        # Get all member_ids currently associated with users
        users_query = supabase.table("users").select("id, member_id").not_.is_("member_id", "null")
        if exclude_user_id:
            users_query = users_query.neq("id", exclude_user_id)
        linked_res = users_query.execute()

        already_linked_ids = {u["member_id"] for u in (linked_res.data or []) if u.get("member_id")}
        return [m for m in all_members if m["id"] not in already_linked_ids]
    except Exception as e:
        print(f"Error fetching available members: {e}")
        return []


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def list_users(
    request: Request,
    role: str = "all",
    q: str = "",
    user: dict = Depends(require_admin)
):
    """Lists user accounts with role filters and live search."""
    users = fetch_users_data(role_filter=role, search_query=q)

    # Compute overall statistics
    all_users = fetch_users_data(role_filter="all")
    stats = {
        "total": len(all_users),
        "admins": sum(1 for u in all_users if u.get("role") == "Admin" and u.get("is_active")),
        "exco": sum(1 for u in all_users if u.get("role") == "Exco" and u.get("is_active")),
        "inactive": sum(1 for u in all_users if not u.get("is_active"))
    }

    context = {
        "request": request,
        "current_user": user,
        "users": users,
        "active_role": role,
        "search_query": q,
        "stats": stats,
        "active_page": "users"
    }
    return templates.TemplateResponse(request, "partials/users.html", context)


@router.get("/new", response_class=HTMLResponse)
async def get_new_user_modal(request: Request, user: dict = Depends(require_admin)):
    """Renders Add User modal partial."""
    available_members = get_available_members()
    context = {
        "request": request,
        "current_user": user,
        "available_members": available_members,
        "roles": USER_ROLES
    }
    return templates.TemplateResponse(request, "partials/user_modal.html", context)


@router.post("", response_class=HTMLResponse)
@router.post("/", response_class=HTMLResponse)
async def create_user(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    role: str = Form("Exco"),
    member_id: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
    is_active: str = Form("false"),
    admin_user: dict = Depends(require_admin)
):
    """Creates a new user account with duplicate username/email guards and password validation."""
    clean_username = username.strip().lower()
    clean_email = email.strip().lower()
    clean_name = full_name.strip()
    active_bool = is_active.lower() in ["true", "1", "on"]
    clean_member_id = int(member_id) if member_id and member_id.strip().isdigit() else None

    # Helper to re-render modal with error
    def render_modal_error(err_msg: str, status_code: int = 422):
        available_members = get_available_members()
        context = {
            "request": request,
            "current_user": admin_user,
            "error": err_msg,
            "available_members": available_members,
            "roles": USER_ROLES,
            "form_data": {
                "full_name": clean_name,
                "username": clean_username,
                "email": clean_email,
                "role": role,
                "member_id": str(clean_member_id) if clean_member_id else "",
                "is_active": active_bool
            }
        }
        return templates.TemplateResponse(request, "partials/user_modal.html", context, status_code=status_code)

    # Validation Checks
    if not clean_username or len(clean_username) < 3:
        return render_modal_error("Username must be at least 3 characters.")

    if password != confirm_password:
        return render_modal_error("Passwords do not match.")

    valid_pw, pw_err = validate_password_strength(password)
    if not valid_pw:
        return render_modal_error(pw_err)

    if supabase:
        try:
            # Check unique username
            existing_user = supabase.table("users").select("id").ilike("username", clean_username).execute()
            if existing_user.data:
                return render_modal_error(f"Username '@{clean_username}' is already taken.")

            # Check unique email
            existing_email = supabase.table("users").select("id").ilike("email", clean_email).execute()
            if existing_email.data:
                return render_modal_error(f"Email '{clean_email}' is already registered to another account.")

            # Check 1-to-1 member linking
            if clean_member_id:
                existing_link = supabase.table("users").select("id").eq("member_id", clean_member_id).execute()
                if existing_link.data:
                    return render_modal_error("Selected club member is already linked to another user account.")

            # Hash Password (600,000 PBKDF2 iterations)
            pw_hash = hash_password(password)

            supabase.table("users").insert({
                "full_name": clean_name,
                "username": clean_username,
                "email": clean_email,
                "password_hash": pw_hash,
                "role": role if role in USER_ROLES else "Exco",
                "member_id": clean_member_id,
                "is_active": active_bool,
                "must_change_password": False
            }).execute()

        except Exception as e:
            return render_modal_error(f"Database error: {str(e)}")
    else:
        if any(u["username"].lower() == clean_username for u in _MOCK_USERS):
            return render_modal_error(f"Username '@{clean_username}' is already taken.")
        if any(u["email"].lower() == clean_email for u in _MOCK_USERS):
            return render_modal_error(f"Email '{clean_email}' is already registered to another account.")
        new_u = {
            "id": len(_MOCK_USERS) + 1,
            "full_name": clean_name,
            "username": clean_username,
            "email": clean_email,
            "password_hash": hash_password(password),
            "role": role if role in USER_ROLES else "Exco",
            "member_id": clean_member_id,
            "is_active": active_bool,
            "must_change_password": False,
            "last_login": None,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "members": None
        }
        _MOCK_USERS.append(new_u)

    # Return refreshed table partial with toast alert
    users = fetch_users_data()
    stats = {
        "total": len(users),
        "admins": sum(1 for u in users if u.get("role") == "Admin" and u.get("is_active")),
        "exco": sum(1 for u in users if u.get("role") == "Exco" and u.get("is_active")),
        "inactive": sum(1 for u in users if not u.get("is_active"))
    }
    context = {
        "request": request,
        "current_user": admin_user,
        "users": users,
        "active_role": "all",
        "stats": stats,
        "active_page": "users",
        "success_message": f"User account @{clean_username} created successfully."
    }
    return templates.TemplateResponse(request, "partials/users.html", context)


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def get_edit_user_modal(request: Request, user_id: int, admin_user: dict = Depends(require_admin)):
    """Renders Edit User modal partial."""
    if not supabase:
        raise HTTPException(status_code=404, detail="Database not configured")

    res = supabase.table("users").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    target_user = res.data[0]
    available_members = get_available_members(exclude_user_id=user_id)

    context = {
        "request": request,
        "current_user": admin_user,
        "target_user": target_user,
        "available_members": available_members,
        "roles": USER_ROLES
    }
    return templates.TemplateResponse(request, "partials/user_edit_modal.html", context)


@router.post("/{user_id}", response_class=HTMLResponse)
async def update_user(
    request: Request,
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form("Exco"),
    member_id: str = Form(""),
    is_active: str = Form("false"),
    must_change_password: str = Form("false"),
    admin_user: dict = Depends(require_admin)
):
    """Updates user profile, role, active status, with self-lockout prevention."""
    clean_name = full_name.strip()
    clean_email = email.strip().lower()
    active_bool = is_active.lower() in ["true", "1", "on"]
    must_change_bool = must_change_password.lower() in ["true", "1", "on"]
    clean_member_id = int(member_id) if member_id and member_id.strip().isdigit() else None

    # Fetch existing record
    target_res = supabase.table("users").select("*").eq("id", user_id).execute() if supabase else None
    if not target_res or not target_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    target_user = target_res.data[0]

    def render_edit_error(err_msg: str, status_code: int = 422):
        available_members = get_available_members(exclude_user_id=user_id)
        target_user_mod = {**target_user, "full_name": clean_name, "email": clean_email, "role": role, "member_id": clean_member_id, "is_active": active_bool}
        context = {
            "request": request,
            "current_user": admin_user,
            "target_user": target_user_mod,
            "available_members": available_members,
            "error": err_msg
        }
        return templates.TemplateResponse(request, "partials/user_edit_modal.html", context, status_code=status_code)

    # Guard 1: Admin cannot deactivate their own account
    if admin_user.get("id") == user_id and not active_bool:
        return render_edit_error("Self-deactivation prevented: You cannot deactivate your own account.")

    # Guard 2: Admin cannot demote their own account
    if admin_user.get("id") == user_id and role != "Admin":
        return render_edit_error("You cannot demote your own Administrator privileges.")

    # Guard 3: Cannot demote or deactivate the last remaining active Admin
    if target_user.get("role") == "Admin" and (role != "Admin" or not active_bool):
        admins_res = supabase.table("users").select("id").eq("role", "Admin").eq("is_active", True).execute()
        active_admins = admins_res.data or []
        if len(active_admins) <= 1:
            return render_edit_error("Cannot modify role: System requires at least one active Administrator.")

    if supabase:
        try:
            # Check unique email
            existing_email = supabase.table("users").select("id").ilike("email", clean_email).neq("id", user_id).execute()
            if existing_email.data:
                return render_edit_error(f"Email '{clean_email}' is already registered to another user.")

            # Check 1-to-1 member linking
            if clean_member_id:
                existing_link = supabase.table("users").select("id").eq("member_id", clean_member_id).neq("id", user_id).execute()
                if existing_link.data:
                    return render_edit_error("Selected club member is already linked to another user account.")

            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            supabase.table("users").update({
                "full_name": clean_name,
                "email": clean_email,
                "role": role if role in USER_ROLES else "Exco",
                "member_id": clean_member_id,
                "is_active": active_bool,
                "must_change_password": must_change_bool,
                "updated_at": now_iso
            }).eq("id", user_id).execute()

        except Exception as e:
            return render_edit_error(f"Database error: {str(e)}")

    # Return refreshed table partial with toast alert
    users = fetch_users_data()
    stats = {
        "total": len(users),
        "admins": sum(1 for u in users if u.get("role") == "Admin" and u.get("is_active")),
        "exco": sum(1 for u in users if u.get("role") == "Exco" and u.get("is_active")),
        "inactive": sum(1 for u in users if not u.get("is_active"))
    }
    context = {
        "request": request,
        "current_user": admin_user,
        "users": users,
        "active_role": "all",
        "stats": stats,
        "active_page": "users",
        "success_message": f"User account @{target_user['username']} updated successfully."
    }
    return templates.TemplateResponse(request, "partials/users.html", context)


@router.get("/{user_id}/reset-password", response_class=HTMLResponse)
async def get_reset_password_modal(request: Request, user_id: int, admin_user: dict = Depends(require_admin)):
    """Renders Admin Password Reset modal."""
    if not supabase:
        raise HTTPException(status_code=404, detail="Database not configured")

    res = supabase.table("users").select("id, username, full_name").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    context = {
        "request": request,
        "current_user": admin_user,
        "target_user": res.data[0]
    }
    return templates.TemplateResponse(request, "partials/user_reset_password_modal.html", context)


@router.post("/{user_id}/reset-password", response_class=HTMLResponse)
async def reset_user_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    must_change_password: str = Form("false"),
    admin_user: dict = Depends(require_admin)
):
    """Resets user's password with administrative authority."""
    target_res = supabase.table("users").select("id, username, full_name").eq("id", user_id).execute() if supabase else None
    if not target_res or not target_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    target_user = target_res.data[0]

    def render_reset_error(err_msg: str, status_code: int = 422):
        context = {
            "request": request,
            "current_user": admin_user,
            "target_user": target_user,
            "error": err_msg
        }
        return templates.TemplateResponse(request, "partials/user_reset_password_modal.html", context, status_code=status_code)

    if new_password != confirm_password:
        return render_reset_error("Passwords do not match.")

    valid_pw, pw_err = validate_password_strength(new_password)
    if not valid_pw:
        return render_reset_error(pw_err)

    if supabase:
        try:
            pw_hash = hash_password(new_password)
            must_change_bool = must_change_password.lower() in ["true", "1", "on"]
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            supabase.table("users").update({
                "password_hash": pw_hash,
                "must_change_password": must_change_bool,
                "updated_at": now_iso
            }).eq("id", user_id).execute()
        except Exception as e:
            return render_reset_error(f"Database error: {str(e)}")

    users = fetch_users_data()
    stats = {
        "total": len(users),
        "admins": sum(1 for u in users if u.get("role") == "Admin" and u.get("is_active")),
        "exco": sum(1 for u in users if u.get("role") == "Exco" and u.get("is_active")),
        "inactive": sum(1 for u in users if not u.get("is_active"))
    }
    context = {
        "request": request,
        "current_user": admin_user,
        "users": users,
        "active_role": "all",
        "stats": stats,
        "active_page": "users",
        "success_message": f"Password for @{target_user['username']} has been reset."
    }
    return templates.TemplateResponse(request, "partials/users.html", context)


@router.get("/{user_id}/delete-confirm", response_class=HTMLResponse)
async def get_delete_user_modal(request: Request, user_id: int, admin_user: dict = Depends(require_admin)):
    """Renders Delete Confirmation modal."""
    if not supabase:
        raise HTTPException(status_code=404, detail="Database not configured")

    res = supabase.table("users").select("id, username, full_name, role").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    context = {
        "request": request,
        "current_user": admin_user,
        "target_user": res.data[0]
    }
    return templates.TemplateResponse(request, "partials/user_delete_modal.html", context)


@router.post("/{user_id}/delete", response_class=HTMLResponse)
async def delete_user(request: Request, user_id: int, admin_user: dict = Depends(require_admin)):
    """Permanently deletes a user account with strict Self-Deletion & Last Admin guardrails."""
    target_res = supabase.table("users").select("id, username, full_name, role").eq("id", user_id).execute() if supabase else None
    if not target_res or not target_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    target_user = target_res.data[0]

    def render_delete_error(err_msg: str, status_code: int = 422):
        context = {
            "request": request,
            "current_user": admin_user,
            "target_user": target_user,
            "error": err_msg
        }
        return templates.TemplateResponse(request, "partials/user_delete_modal.html", context, status_code=status_code)

    # Guard 1: Cannot delete self
    if admin_user.get("id") == user_id:
        return render_delete_error("Self-deletion prevented: You cannot delete your own logged-in account.")

    # Guard 2: Cannot delete last remaining active Admin
    if target_user.get("role") == "Admin":
        admins_res = supabase.table("users").select("id").eq("role", "Admin").eq("is_active", True).execute()
        active_admins = admins_res.data or []
        if len(active_admins) <= 1:
            return render_delete_error("Last Admin Guard: Cannot delete the last active Administrator.")

    if supabase:
        try:
            supabase.table("users").delete().eq("id", user_id).execute()
        except Exception as e:
            return render_delete_error(f"Database error: {str(e)}")

    users = fetch_users_data()
    stats = {
        "total": len(users),
        "admins": sum(1 for u in users if u.get("role") == "Admin" and u.get("is_active")),
        "exco": sum(1 for u in users if u.get("role") == "Exco" and u.get("is_active")),
        "inactive": sum(1 for u in users if not u.get("is_active"))
    }
    context = {
        "request": request,
        "current_user": admin_user,
        "users": users,
        "active_role": "all",
        "stats": stats,
        "active_page": "users",
        "success_message": f"User account @{target_user['username']} permanently deleted."
    }
    return templates.TemplateResponse(request, "partials/users.html", context)


@router.get("/profile/settings", response_class=HTMLResponse)
async def get_profile_settings_modal(request: Request, current_user: dict = Depends(get_current_user)):
    """Renders Self-Service Account Settings & Password Change Modal for currently logged-in user."""
    context = {
        "request": request,
        "current_user": current_user
    }
    return templates.TemplateResponse(request, "partials/user_profile_modal.html", context)


@router.post("/profile/password", response_class=HTMLResponse)
async def update_own_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Allows authenticated users to update their own password."""
    def render_profile_error(err_msg: str, status_code: int = 422):
        context = {
            "request": request,
            "current_user": current_user,
            "error": err_msg
        }
        return templates.TemplateResponse(request, "partials/user_profile_modal.html", context, status_code=status_code)

    if current_user.get("is_passkey") or not current_user.get("id"):
        return render_profile_error("Shared passkey accounts cannot update individual credentials.")

    if new_password != confirm_password:
        return render_profile_error("New passwords do not match.")

    valid_pw, pw_err = validate_password_strength(new_password)
    if not valid_pw:
        return render_profile_error(pw_err)

    if supabase:
        try:
            res = supabase.table("users").select("password_hash").eq("id", current_user["id"]).execute()
            if not res.data:
                return render_profile_error("User record not found.")

            stored_hash = res.data[0].get("password_hash", "")
            if not verify_password(current_password, stored_hash):
                return render_profile_error("Current password incorrect.")

            new_hash = hash_password(new_password)
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            supabase.table("users").update({
                "password_hash": new_hash,
                "must_change_password": False,
                "updated_at": now_iso
            }).eq("id", current_user["id"]).execute()

        except Exception as e:
            return render_profile_error(f"Error updating password: {str(e)}")
    else:
        if current_password not in ["AdminPass@123", "Admin@12345"]:
            return render_profile_error("Current password incorrect.")

    # Return success response that closes modal and displays toast
    return HTMLResponse(
        content='''
        <div class="toast-trigger hidden" data-toast-message="Your password has been updated successfully!" data-toast-type="success"></div>
        <script>
            const m = document.getElementById("modal-backdrop");
            if (m) m.remove();
        </script>
        ''',
        status_code=200
    )
