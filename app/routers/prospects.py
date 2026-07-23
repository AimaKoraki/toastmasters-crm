from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..config import supabase
from ..dependencies import get_current_user

router = APIRouter(prefix="/prospects", tags=["prospects"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def get_prospects(request: Request, user=Depends(get_current_user)):
    # Fetch prospects from Supabase (mocking for now if DB not seeded)
    prospects = []
    if supabase:
        response = supabase.table("members").select("*").eq("status", "Prospect").execute()
        prospects = response.data
    return templates.TemplateResponse(request, "partials/prospects.html", {"prospects": prospects})

@router.post("/", response_class=HTMLResponse)
async def add_prospect(
    request: Request, 
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    user=Depends(get_current_user)
):
    if supabase:
        new_prospect = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "status": "Prospect"
        }
        response = supabase.table("members").insert(new_prospect).execute()
        # Optionally, add to prospect_logs table
        if response.data:
            member_id = response.data[0]["id"]
            supabase.table("prospect_logs").insert({"member_id": member_id, "stage": "1st Visit"}).execute()

    # Re-fetch list
    prospects = []
    if supabase:
        res = supabase.table("members").select("*").eq("status", "Prospect").execute()
        prospects = res.data

    return templates.TemplateResponse(request, "partials/prospects.html", {"prospects": prospects})
