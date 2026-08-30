from fastapi import APIRouter, Request, Form, Depends, HTTPException, status as http_status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import supabase
from app.dependencies import get_current_user
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

MEMBER_STATUSES = ["Active", "Inactive", "Alumni"]
PATHWAY_LEVELS = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "DTM"]


def calculate_renewal_status(created_at_str: str = None) -> dict:
    """
    Computes Toastmasters semi-annual renewal status (March 31 & September 30 cycles).
    Returns badge color, label, and urgency.
    """
    today = datetime.date.today()
    current_year = today.year

    # Current cycle deadlines
    mar_deadline = datetime.date(current_year, 3, 31)
    sep_deadline = datetime.date(current_year, 9, 30)

    # Determine next upcoming cycle deadline
    if today <= mar_deadline:
        next_deadline = mar_deadline
        cycle_name = f"March {current_year}"
    elif today <= sep_deadline:
        next_deadline = sep_deadline
        cycle_name = f"September {current_year}"
    else:
        next_deadline = datetime.date(current_year + 1, 3, 31)
        cycle_name = f"March {current_year + 1}"

    days_remaining = (next_deadline - today).days

    if days_remaining <= 30:
        return {
            "cycle": cycle_name,
            "status": "Due Soon",
            "days_left": days_remaining,
            "badge_class": "bg-rose-50 text-rose-700 border-rose-200",
            "dot_class": "bg-rose-500"
        }
    elif days_remaining <= 60:
        return {
            "cycle": cycle_name,
            "status": "Upcoming",
            "days_left": days_remaining,
            "badge_class": "bg-amber-50 text-amber-800 border-amber-200",
            "dot_class": "bg-amber-500"
        }
    else:
        return {
            "cycle": cycle_name,
            "status": "Current",
            "days_left": days_remaining,
            "badge_class": "bg-emerald-50 text-emerald-700 border-emerald-200",
            "dot_class": "bg-emerald-500"
        }


def fetch_members_data(status_filter: str = "all") -> list:
    """
    Fetches non-prospect club members (Active, Inactive, Alumni) from Supabase,
    attaching computed renewal status and formatting.
    """
    members_list = []
    if not supabase:
        return members_list

    try:
        query = supabase.table("members").select("*")
        if status_filter in MEMBER_STATUSES:
            query = query.eq("status", status_filter)
        else:
            # Exclude raw Prospects from the Member Directory unless specifically requested
            query = query.neq("status", "Prospect")

        res = query.order("full_name", desc=False).execute()
        if res.data:
            for m in res.data:
                member_dict = dict(m)
                member_dict["renewal_info"] = calculate_renewal_status(member_dict.get("created_at"))
                members_list.append(member_dict)
    except Exception as e:
        print(f"Error fetching members: {e}")

    return members_list


@router.get("", response_class=HTMLResponse)
async def get_members_directory(
    request: Request,
    status: str = "all",
    user=Depends(get_current_user)
):
    """
    Renders the Member Directory table partial with status filters and summary metrics.
    """
    members = fetch_members_data(status_filter=status)

    # Calculate roster distribution counts across all non-prospect members
    all_members = fetch_members_data(status_filter="all")
    active_count = sum(1 for m in all_members if m.get("status") == "Active")
    inactive_count = sum(1 for m in all_members if m.get("status") == "Inactive")
    alumni_count = sum(1 for m in all_members if m.get("status") == "Alumni")

    context = {
        "request": request,
        "members": members,
        "active_status": status,
        "statuses": MEMBER_STATUSES,
        "pathway_levels": PATHWAY_LEVELS,
        "active_page": "members",
        "stats": {
            "total": len(all_members),
            "active": active_count,
            "inactive": inactive_count,
            "alumni": alumni_count,
        }
    }
    return templates.TemplateResponse(request, "partials/members.html", context)


@router.get("/new", response_class=HTMLResponse)
async def get_new_member_modal(request: Request, user=Depends(get_current_user)):
    """
    Renders the standalone Add Member modal partial for HTMX injection into #modal-container.
    """
    context = {
        "request": request,
        "statuses": MEMBER_STATUSES,
        "pathway_levels": PATHWAY_LEVELS
    }
    return templates.TemplateResponse(request, "partials/member_modal.html", context)


@router.post("", response_class=HTMLResponse)
@router.post("/", response_class=HTMLResponse)
async def create_member(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    status: str = Form("Active"),
    pathway_level: str = Form("Level 1"),
    user=Depends(get_current_user)
):
    """
    Creates a new member in the members table and returns the refreshed members directory partial.
    """
    if status not in MEMBER_STATUSES:
        status = "Active"
    if pathway_level not in PATHWAY_LEVELS:
        pathway_level = "Level 1"

    cleaned_email = email.strip().lower()
    cleaned_name = full_name.strip()

    if supabase:
        try:
            # Check for existing email to avoid silent or unhandled DB constraint errors (case-insensitive)
            existing = supabase.table("members").select("id, full_name, status").ilike("email", cleaned_email).execute()
            if existing.data:
                existing_record = existing.data[0]
                record_type = "member" if existing_record.get("status") == "Active" else "guest"
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"A {record_type} with email '{cleaned_email}' already exists ({existing_record.get('full_name')})."
                )

            new_member_payload = {
                "full_name": cleaned_name,
                "email": cleaned_email,
                "phone": phone.strip() if phone else None,
                "status": status,
                "pathway_level": pathway_level
            }
            supabase.table("members").insert(new_member_payload).execute()
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error creating member: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create member: {str(e)}"
            )

    members = fetch_members_data(status_filter="all")
    all_members = members
    active_count = sum(1 for m in all_members if m.get("status") == "Active")
    inactive_count = sum(1 for m in all_members if m.get("status") == "Inactive")
    alumni_count = sum(1 for m in all_members if m.get("status") == "Alumni")

    context = {
        "request": request,
        "members": members,
        "active_status": "all",
        "statuses": MEMBER_STATUSES,
        "pathway_levels": PATHWAY_LEVELS,
        "active_page": "members",
        "success_message": f"Member '{full_name.strip()}' successfully added.",
        "stats": {
            "total": len(all_members),
            "active": active_count,
            "inactive": inactive_count,
            "alumni": alumni_count,
        }
    }
    return templates.TemplateResponse(request, "partials/members.html", context)


@router.get("/{member_id}/edit", response_class=HTMLResponse)
async def get_edit_member_modal(
    request: Request,
    member_id: int,
    user=Depends(get_current_user)
):
    """
    Renders the standalone Edit Member modal partial populated with member details.
    """
    member = None
    if supabase:
        try:
            res = supabase.table("members").select("*").eq("id", member_id).execute()
            if res.data:
                member = res.data[0]
        except Exception as e:
            print(f"Error fetching member for edit: {e}")

    if not member:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID #{member_id} not found."
        )

    context = {
        "request": request,
        "member": member,
        "statuses": MEMBER_STATUSES,
        "pathway_levels": PATHWAY_LEVELS
    }
    return templates.TemplateResponse(request, "partials/member_edit_modal.html", context)


@router.post("/{member_id}", response_class=HTMLResponse)
async def update_member(
    request: Request,
    member_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    status: str = Form("Active"),
    pathway_level: str = Form("Level 1"),
    user=Depends(get_current_user)
):
    """
    Updates an existing member's contact, status, and Pathways advancement.
    """
    if status not in MEMBER_STATUSES:
        status = "Active"
    if pathway_level not in PATHWAY_LEVELS:
        pathway_level = "Level 1"

    cleaned_email = email.strip().lower()
    cleaned_name = full_name.strip()

    if supabase:
        try:
            # Check for duplicate email across other members & prospects
            existing = supabase.table("members").select("id, full_name, status").ilike("email", cleaned_email).neq("id", member_id).execute()
            if existing.data:
                existing_record = existing.data[0]
                record_type = "member" if existing_record.get("status") == "Active" else "guest"
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot update: Email '{cleaned_email}' is already in use by {record_type} '{existing_record.get('full_name')}'."
                )

            update_payload = {
                "full_name": cleaned_name,
                "email": cleaned_email,
                "phone": phone.strip() if phone else None,
                "status": status,
                "pathway_level": pathway_level
            }
            res = supabase.table("members").update(update_payload).eq("id", member_id).execute()
            if not res.data:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Member #{member_id} not found to update."
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error updating member #{member_id}: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update member: {str(e)}"
            )

    members = fetch_members_data(status_filter="all")
    all_members = members
    active_count = sum(1 for m in all_members if m.get("status") == "Active")
    inactive_count = sum(1 for m in all_members if m.get("status") == "Inactive")
    alumni_count = sum(1 for m in all_members if m.get("status") == "Alumni")

    context = {
        "request": request,
        "members": members,
        "active_status": "all",
        "statuses": MEMBER_STATUSES,
        "pathway_levels": PATHWAY_LEVELS,
        "active_page": "members",
        "success_message": f"Member '{full_name.strip()}' profile successfully updated.",
        "stats": {
            "total": len(all_members),
            "active": active_count,
            "inactive": inactive_count,
            "alumni": alumni_count,
        }
    }
    return templates.TemplateResponse(request, "partials/members.html", context)
