from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..config import supabase
from ..dependencies import get_current_user

router = APIRouter(prefix="/roles", tags=["roles"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def get_roles(request: Request, user=Depends(get_current_user)):
    roles_matrix = []
    # Real implementation would join members, meetings, and role_assignments
    # and compute the frequency matrix. For now, returning a static structure for HTMX response.
    return templates.TemplateResponse(request, "partials/roles.html", {"matrix": roles_matrix, "active_page": "role_matrix"})

@router.post("/assign", response_class=HTMLResponse)
async def assign_role(
    request: Request,
    meeting_id: int = Form(...),
    member_id: int = Form(...),
    role_id: int = Form(...),
    speech_title: str = Form(""),
    user=Depends(get_current_user)
):
    if supabase:
        new_assignment = {
            "meeting_id": meeting_id,
            "member_id": member_id,
            "role_id": role_id,
            "speech_title": speech_title
        }
        supabase.table("role_assignments").insert(new_assignment).execute()
        
    # Re-fetch matrix...
    return templates.TemplateResponse(request, "partials/roles.html", {"matrix": [], "active_page": "role_matrix"})
