from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..config import supabase
from ..dependencies import get_current_user

router = APIRouter(prefix="/prospects", tags=["prospects"])
templates = Jinja2Templates(directory="app/templates")

STAGES = ["1st Visit", "2nd Visit", "Form Sent", "Payment Pending", "Onboarded"]

def fetch_prospects_data(stage_filter: str = "all"):
    """
    Fetches all prospects from Supabase, joining their latest stage,
    notes, last contacted timestamp, and stage transition history.
    """
    prospects = []
    if not supabase:
        return prospects

    try:
        # Fetch members with status Prospect or recently Onboarded
        res = supabase.table("members").select("*").order("created_at", desc=True).execute()
        all_members = res.data or []

        # Fetch all prospect logs sorted chronologically descending
        logs_res = supabase.table("prospect_logs").select("*").order("created_at", desc=True).execute()
        all_logs = logs_res.data or []

        # Group logs by member_id
        member_logs = {}
        for log in all_logs:
            mid = log.get("member_id")
            if mid not in member_logs:
                member_logs[mid] = []
            member_logs[mid].append(log)

        # Build composite prospect list
        for m in all_members:
            mid = m["id"]
            logs = member_logs.get(mid, [])
            
            # Determine latest stage from logs or default to '1st Visit'
            if logs:
                latest_log = logs[0]
                current_stage = latest_log.get("stage", "1st Visit")
                latest_notes = latest_log.get("notes", "")
                last_contacted = latest_log.get("last_contacted") or latest_log.get("created_at", "")
            else:
                current_stage = "1st Visit" if m.get("status") == "Prospect" else "Onboarded"
                latest_notes = ""
                last_contacted = m.get("created_at", "")

            # Filter criteria:
            # If status is Active and stage is not in logs as Onboarded, skip (regular member)
            if m.get("status") != "Prospect" and current_stage != "Onboarded":
                continue

            # Calculate next logical stage in pipeline
            try:
                current_idx = STAGES.index(current_stage)
                next_stage = STAGES[current_idx + 1] if current_idx < len(STAGES) - 1 else None
            except ValueError:
                next_stage = None

            prospect_entry = {
                "id": mid,
                "full_name": m.get("full_name", ""),
                "email": m.get("email", ""),
                "phone": m.get("phone", ""),
                "status": m.get("status", "Prospect"),
                "stage": current_stage,
                "notes": latest_notes,
                "last_contacted": last_contacted,
                "created_at": m.get("created_at", ""),
                "history": logs,
                "history_count": len(logs),
                "next_stage": next_stage
            }

            # Apply stage filter
            if stage_filter == "all" or stage_filter == "" or prospect_entry["stage"].lower() == stage_filter.lower():
                prospects.append(prospect_entry)

    except Exception as e:
        print(f"Error fetching prospects data: {e}")

    return prospects


@router.get("/", response_class=HTMLResponse)
async def get_prospects(request: Request, stage: str = "all", user=Depends(get_current_user)):
    prospects = fetch_prospects_data(stage_filter=stage)
    context = {
        "request": request,
        "prospects": prospects,
        "stages": STAGES,
        "active_stage": stage,
        "active_page": "guests"
    }
    return templates.TemplateResponse(request, "partials/prospects.html", context)


@router.get("/new", response_class=HTMLResponse)
async def get_new_prospect_modal(request: Request, user=Depends(get_current_user)):
    """
    Returns the Add New Guest modal partial (supports Dashboard Quick Action)
    """
    context = {
        "request": request,
        "stages": STAGES
    }
    return templates.TemplateResponse(request, "partials/prospect_modal.html", context)


@router.post("/", response_class=HTMLResponse)
async def add_prospect(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    notes: str = Form(""),
    initial_stage: str = Form("1st Visit"),
    user=Depends(get_current_user)
):
    if initial_stage not in STAGES:
        initial_stage = "1st Visit"

    if supabase:
        try:
            new_prospect = {
                "full_name": full_name.strip(),
                "email": email.strip(),
                "phone": phone.strip() if phone else None,
                "status": "Prospect" if initial_stage != "Onboarded" else "Active"
            }
            res = supabase.table("members").insert(new_prospect).execute()
            if res.data:
                member_id = res.data[0]["id"]
                log_entry = {
                    "member_id": member_id,
                    "stage": initial_stage,
                    "notes": notes.strip() if notes else "Guest registered"
                }
                supabase.table("prospect_logs").insert(log_entry).execute()
        except Exception as e:
            print(f"Error inserting new prospect: {e}")

    prospects = fetch_prospects_data(stage_filter="all")
    context = {
        "request": request,
        "prospects": prospects,
        "stages": STAGES,
        "active_stage": "all",
        "active_page": "guests"
    }
    return templates.TemplateResponse(request, "partials/prospects.html", context)


@router.post("/{prospect_id}/stage", response_class=HTMLResponse)
async def update_prospect_stage(
    request: Request,
    prospect_id: int,
    stage: str = Form(...),
    notes: str = Form(""),
    user=Depends(get_current_user)
):
    """
    Progresses a prospect to a new pipeline stage, logs the transition with notes,
    and automatically upgrades the member's status to 'Active' when 'Onboarded'.
    """
    if stage not in STAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage. Must be one of: {', '.join(STAGES)}"
        )

    if supabase:
        try:
            # 1. Insert stage transition record in prospect_logs
            log_data = {
                "member_id": prospect_id,
                "stage": stage,
                "notes": notes.strip() if notes else f"Advanced to {stage}"
            }
            supabase.table("prospect_logs").insert(log_data).execute()

            # 2. If transitioning to 'Onboarded', update member status to 'Active'
            if stage == "Onboarded":
                supabase.table("members").update({
                    "status": "Active"
                }).eq("id", prospect_id).execute()
            else:
                # Ensure status remains 'Prospect' if not Onboarded
                supabase.table("members").update({
                    "status": "Prospect"
                }).eq("id", prospect_id).execute()

        except Exception as e:
            print(f"Error updating prospect stage: {e}")

    prospects = fetch_prospects_data(stage_filter="all")
    context = {
        "request": request,
        "prospects": prospects,
        "stages": STAGES,
        "active_stage": "all",
        "active_page": "guests"
    }
    return templates.TemplateResponse(request, "partials/prospects.html", context)


@router.get("/{prospect_id}/history", response_class=HTMLResponse)
async def get_prospect_history(
    request: Request,
    prospect_id: int,
    user=Depends(get_current_user)
):
    """
    Returns the stage progression history timeline partial for a specific prospect.
    """
    member_data = None
    logs = []

    if supabase:
        try:
            m_res = supabase.table("members").select("*").eq("id", prospect_id).execute()
            if m_res.data:
                member_data = m_res.data[0]

            l_res = supabase.table("prospect_logs").select("*").eq("member_id", prospect_id).order("created_at", desc=True).execute()
            logs = l_res.data or []
        except Exception as e:
            print(f"Error fetching history for prospect {prospect_id}: {e}")

    context = {
        "request": request,
        "member": member_data,
        "logs": logs,
        "stages": STAGES
    }
    return templates.TemplateResponse(request, "partials/prospect_history_modal.html", context)
