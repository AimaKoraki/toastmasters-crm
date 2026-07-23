from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..config import supabase
from ..dependencies import get_current_user

router = APIRouter(prefix="/meetings", tags=["meetings"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def get_meetings(request: Request, user=Depends(get_current_user)):
    meetings = []
    if supabase:
        res = supabase.table("meetings").select("*").order("meeting_date", desc=True).execute()
        meetings = res.data
    return templates.TemplateResponse(request, "partials/meetings.html", {"meetings": meetings})

@router.post("/", response_class=HTMLResponse)
async def create_meeting(
    request: Request,
    meeting_number: int = Form(...),
    meeting_date: str = Form(...),
    theme: str = Form(""),
    user=Depends(get_current_user)
):
    if supabase:
        new_meeting = {
            "meeting_number": meeting_number,
            "meeting_date": meeting_date,
            "theme": theme
        }
        supabase.table("meetings").insert(new_meeting).execute()

    meetings = []
    if supabase:
        res = supabase.table("meetings").select("*").order("meeting_date", desc=True).execute()
        meetings = res.data
        
    return templates.TemplateResponse(request, "partials/meetings.html", {"meetings": meetings})
