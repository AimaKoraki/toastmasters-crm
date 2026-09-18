from fastapi import Request, HTTPException, status, Depends
from app.config import supabase

ROLE_HIERARCHY = {
    "Viewer": 1,
    "Exco": 2,
    "Admin": 3
}


def get_current_user(request: Request) -> dict:
    """
    Authenticates the current request from session.
    Keeps cookie lightweight: looks up fresh identity attributes from DB.
    """
    authenticated = request.session.get("authenticated")
    if not authenticated:
        if request.headers.get("HX-Request"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"HX-Redirect": "/login"}
            )
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )

    # Legacy or emergency Exco passkey session
    if request.session.get("is_passkey") or "user_id" not in request.session:
        return {
            "id": 0,
            "username": "exco_passkey",
            "email": "exco@apiitkandy.club",
            "full_name": "Exco Officer",
            "role": "Exco",
            "is_active": True,
            "must_change_password": False,
            "is_passkey": True
        }

    user_id = request.session.get("user_id")

    if supabase:
        try:
            res = supabase.table("users").select(
                "id, username, email, full_name, role, member_id, is_active, must_change_password, last_login"
            ).eq("id", user_id).execute()

            if not res.data or len(res.data) == 0:
                request.session.clear()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={"HX-Redirect": "/login"}
                )

            user = res.data[0]
            if not user.get("is_active", True):
                request.session.clear()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This account has been deactivated. Contact an administrator."
                )

            return user
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error fetching user session from DB: {e}")
            # Fallback to stored session if DB query temporarily fails
            pass

    # Fallback user if DB is unavailable or mock environment
    return {
        "id": user_id,
        "username": request.session.get("username", "user"),
        "email": request.session.get("email", "user@apiitkandy.club"),
        "full_name": request.session.get("full_name", "Club User"),
        "role": request.session.get("role", "Exco"),
        "is_active": True,
        "must_change_password": False
    }


def require_role(min_role: str = "Exco"):
    """
    Parameterized role-checker enforcing role hierarchy:
    Viewer (1) < Exco (2) < Admin (3).
    """
    def role_checker(request: Request, user: dict = Depends(get_current_user)):
        user_level = ROLE_HIERARCHY.get(user.get("role", "Viewer"), 1)
        required_level = ROLE_HIERARCHY.get(min_role, 2)
        if user_level < required_level:
            error_msg = f"Access restricted: Minimum '{min_role}' role required."
            if request.headers.get("HX-Request"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        return user

    return role_checker


require_admin = require_role("Admin")
require_exco = require_role("Exco")
