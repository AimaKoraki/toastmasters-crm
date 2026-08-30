from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..config import supabase
from ..dependencies import get_current_user

router = APIRouter(prefix="/roles", tags=["roles"])
templates = Jinja2Templates(directory="app/templates")


def fetch_roles_matrix(category_filter: str = "all"):
    """
    Computes cross-tabulation matrix of member role assignments.
    Returns:
      - roles: list of role catalog entries (filtered if category specified)
      - matrix: list of member objects with { member_info, role_counts: {role_id: count}, total_roles }
      - all_members: for dropdown selection
      - all_meetings: for dropdown selection
      - all_roles: all catalog roles regardless of table column filter
    """
    roles = []
    matrix = []
    all_members = []
    all_meetings = []
    all_roles = []

    if not supabase:
        return roles, matrix, all_members, all_meetings, all_roles

    try:
        # 1. Fetch Role Catalog
        cat_res = supabase.table("role_catalog").select("*").order("id").execute()
        all_roles = cat_res.data or []

        # Apply category filter for matrix columns
        if category_filter.lower() != "all" and category_filter != "":
            roles = [r for r in all_roles if r.get("category", "").lower() == category_filter.lower()]
        else:
            roles = all_roles

        # 2. Fetch Members
        mem_res = supabase.table("members").select("*").order("full_name").execute()
        all_members = mem_res.data or []

        # 3. Fetch Meetings
        m_res = supabase.table("meetings").select("*").order("meeting_date", desc=True).execute()
        all_meetings = m_res.data or []

        # 4. Fetch Role Assignments with Joins
        assign_res = supabase.table("role_assignments").select(
            "id, meeting_id, member_id, role_id, speech_title, created_at, meetings(meeting_number, meeting_date, theme), role_catalog(role_name, category)"
        ).order("created_at", desc=True).execute()
        all_assignments = assign_res.data or []

        # Group assignments by member_id
        member_assignments = {}
        for a in all_assignments:
            mid = a.get("member_id")
            if mid not in member_assignments:
                member_assignments[mid] = []
            member_assignments[mid].append(a)

        # 5. Build Matrix Rows
        for mem in all_members:
            mid = mem["id"]
            m_assigns = member_assignments.get(mid, [])

            role_counts = {r["id"]: 0 for r in roles}
            total_roles_all = len(m_assigns)
            
            for a in m_assigns:
                rid = a.get("role_id")
                if rid in role_counts:
                    role_counts[rid] += 1

            matrix.append({
                "id": mid,
                "full_name": mem.get("full_name", ""),
                "email": mem.get("email", ""),
                "status": mem.get("status", "Active"),
                "pathway_level": mem.get("pathway_level", "Level 1"),
                "role_counts": role_counts,
                "total_roles": total_roles_all,
                "recent_assignments": m_assigns[:3]
            })

    except Exception as e:
        print(f"Error computing roles matrix: {e}")

    return roles, matrix, all_members, all_meetings, all_roles


@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse)
async def get_roles(request: Request, category: str = "all", user=Depends(get_current_user)):
    roles, matrix, all_members, all_meetings, all_roles = fetch_roles_matrix(category_filter=category)
    context = {
        "request": request,
        "roles": roles,
        "matrix": matrix,
        "all_members": all_members,
        "all_meetings": all_meetings,
        "all_roles": all_roles,
        "active_category": category,
        "active_page": "role_matrix"
    }
    return templates.TemplateResponse(request, "partials/roles.html", context)


@router.get("/assign", response_class=HTMLResponse)
async def get_assign_role_modal(request: Request, user=Depends(get_current_user)):
    """
    Returns standalone Add Role Assignment modal for Quick Actions or HTMX trigger.
    """
    all_members = []
    all_meetings = []
    all_roles = []

    if supabase:
        try:
            mem_res = supabase.table("members").select("id, full_name, status").order("full_name").execute()
            all_members = mem_res.data or []

            m_res = supabase.table("meetings").select("id, meeting_number, meeting_date, theme").order("meeting_date", desc=True).execute()
            all_meetings = m_res.data or []

            cat_res = supabase.table("role_catalog").select("id, role_name, category").order("id").execute()
            all_roles = cat_res.data or []
        except Exception as e:
            print(f"Error fetching role assignment modal data: {e}")

    context = {
        "request": request,
        "all_members": all_members,
        "all_meetings": all_meetings,
        "all_roles": all_roles
    }
    return templates.TemplateResponse(request, "partials/role_assign_modal.html", context)


@router.post("/assign", response_class=HTMLResponse)
@router.post("", response_class=HTMLResponse)
async def assign_role(
    request: Request,
    user=Depends(get_current_user)
):
    """
    Assigns one or more roles to a member for a given meeting.
    Accepts multiple role_ids from checkboxes.
    Returns granular success/warning based on duplicates detected.
    """
    form = await request.form()
    meeting_id = int(form.get("meeting_id", 0))
    member_id = int(form.get("member_id", 0))
    role_ids = [int(v) for v in form.getlist("role_ids") if v]
    speech_title = form.get("speech_title", "").strip() or None

    added_roles = []
    skipped_roles = []
    success_message = None
    warning_message = None

    if supabase and role_ids:
        try:
            # Fetch role names for feedback messages
            cat_res = supabase.table("role_catalog").select("id, role_name").execute()
            role_name_map = {r["id"]: r["role_name"] for r in (cat_res.data or [])}

            for rid in role_ids:
                # Check for existing duplicate
                existing = supabase.table("role_assignments").select("id").eq(
                    "meeting_id", meeting_id
                ).eq("member_id", member_id).eq("role_id", rid).execute()

                if existing.data:
                    skipped_roles.append(role_name_map.get(rid, f"Role #{rid}"))
                else:
                    supabase.table("role_assignments").insert({
                        "meeting_id": meeting_id,
                        "member_id": member_id,
                        "role_id": rid,
                        "speech_title": speech_title
                    }).execute()
                    added_roles.append(role_name_map.get(rid, f"Role #{rid}"))

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error assigning role(s): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to assign role(s): {str(e)}"
            )

    if added_roles and skipped_roles:
        success_message = f"{len(added_roles)} role(s) assigned: {', '.join(added_roles)}."
        warning_message = f"{len(skipped_roles)} already assigned & skipped: {', '.join(skipped_roles)}."
    elif added_roles:
        success_message = f"{len(added_roles)} role(s) successfully assigned: {', '.join(added_roles)}."
    elif skipped_roles:
        warning_message = f"All selected role(s) already assigned — nothing new added: {', '.join(skipped_roles)}."
    elif not role_ids:
        warning_message = "No roles were selected. Please check at least one role."

    roles, matrix, all_members, all_meetings, all_roles = fetch_roles_matrix(category_filter="all")
    context = {
        "request": request,
        "roles": roles,
        "matrix": matrix,
        "all_members": all_members,
        "all_meetings": all_meetings,
        "all_roles": all_roles,
        "active_category": "all",
        "success_message": success_message,
        "warning_message": warning_message,
        "active_page": "role_matrix"
    }
    return templates.TemplateResponse(request, "partials/roles.html", context)


@router.get("/member/{member_id}/history", response_class=HTMLResponse)
async def get_member_role_history(
    request: Request,
    member_id: int,
    user=Depends(get_current_user)
):
    """
    Returns the role participation timeline for a specific member.
    """
    member = None
    assignments = []

    if supabase:
        try:
            mem_res = supabase.table("members").select("*").eq("id", member_id).execute()
            if mem_res.data:
                member = mem_res.data[0]

            assign_res = supabase.table("role_assignments").select(
                "id, speech_title, created_at, meetings(meeting_number, meeting_date, theme), role_catalog(role_name, category)"
            ).eq("member_id", member_id).order("created_at", desc=True).execute()
            assignments = assign_res.data or []
        except Exception as e:
            print(f"Error fetching member role history: {e}")

    context = {
        "request": request,
        "member": member,
        "assignments": assignments
    }
    return templates.TemplateResponse(request, "partials/member_role_history_modal.html", context)
