from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..config import supabase
from ..dependencies import get_current_user

router = APIRouter(tags=["meetings"])
templates = Jinja2Templates(directory="app/templates")

ATTENDANCE_STATUSES = ["Present", "Absent", "Excused"]


def fetch_meetings_with_stats():
    """
    Fetches all meetings ordered by meeting_date descending,
    and calculates attendance counts for each meeting.
    """
    meetings = []
    if not supabase:
        return meetings

    try:
        m_res = supabase.table("meetings").select("*").order("meeting_date", desc=True).execute()
        meetings = m_res.data or []

        # Fetch all attendance records
        att_res = supabase.table("attendance").select("meeting_id, status").execute()
        all_att = att_res.data or []

        # Group attendance counts by meeting_id
        att_by_meeting = {}
        for a in all_att:
            mid = a.get("meeting_id")
            if mid not in att_by_meeting:
                att_by_meeting[mid] = {"present": 0, "absent": 0, "excused": 0, "guest": 0, "total": 0}
            
            st = a.get("status")
            if st == "Present" or st == "Guest":
                att_by_meeting[mid]["present"] += 1
            elif st == "Absent":
                att_by_meeting[mid]["absent"] += 1
            elif st == "Excused":
                att_by_meeting[mid]["excused"] += 1
            att_by_meeting[mid]["total"] += 1

        for m in meetings:
            mid = m["id"]
            stats = att_by_meeting.get(mid, {"present": 0, "absent": 0, "excused": 0, "guest": 0, "total": 0})
            m["present_count"] = stats["present"]
            m["absent_count"] = stats["absent"]
            m["excused_count"] = stats["excused"]
            m["guest_count"] = stats["guest"]
            m["total_attendance"] = stats["total"]

    except Exception as e:
        print(f"Error fetching meetings with stats: {e}")

    return meetings


@router.get("/meetings", response_class=HTMLResponse)
@router.get("/meetings/", response_class=HTMLResponse)
async def get_meetings(request: Request, user=Depends(get_current_user)):
    meetings = fetch_meetings_with_stats()
    context = {
        "request": request,
        "meetings": meetings,
        "active_page": "attendance"
    }
    return templates.TemplateResponse(request, "partials/meetings.html", context)


@router.get("/meetings/new", response_class=HTMLResponse)
async def get_new_meeting_modal(request: Request, user=Depends(get_current_user)):
    """
    Returns standalone Add Meeting modal for dashboard quick actions.
    """
    return templates.TemplateResponse(request, "partials/meeting_modal.html", {"request": request})


@router.post("/meetings", response_class=HTMLResponse)
@router.post("/meetings/", response_class=HTMLResponse)
async def create_meeting(
    request: Request,
    meeting_number: int = Form(...),
    meeting_date: str = Form(...),
    theme: str = Form(""),
    user=Depends(get_current_user)
):
    if supabase:
        try:
            # Check duplicate meeting number
            existing = supabase.table("meetings").select("id").eq("meeting_number", meeting_number).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Meeting #{meeting_number} is already scheduled."
                )

            new_meeting = {
                "meeting_number": meeting_number,
                "meeting_date": meeting_date,
                "theme": theme.strip() if theme else None
            }
            supabase.table("meetings").insert(new_meeting).execute()
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error creating meeting: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to schedule meeting: {str(e)}"
            )

    meetings = fetch_meetings_with_stats()
    context = {
        "request": request,
        "meetings": meetings,
        "active_page": "attendance",
        "success_message": f"Meeting #{meeting_number} scheduled successfully."
    }
    return templates.TemplateResponse(request, "partials/meetings.html", context)


@router.get("/meetings/attendance", response_class=HTMLResponse)
async def get_latest_meeting_attendance(request: Request, user=Depends(get_current_user)):
    """
    Helper for Dashboard Quick Action: auto-selects the latest meeting and renders its check-in sheet.
    """
    latest_meeting_id = None
    if supabase:
        try:
            m_res = supabase.table("meetings").select("id").order("meeting_date", desc=True).limit(1).execute()
            if m_res.data:
                latest_meeting_id = m_res.data[0]["id"]
        except Exception as e:
            print(f"Error fetching latest meeting: {e}")

    if latest_meeting_id:
        return await get_meeting_attendance_sheet(request, latest_meeting_id, user)
    
    # If no meeting exists yet, return standard meetings partial
    meetings = fetch_meetings_with_stats()
    return templates.TemplateResponse(request, "partials/meetings.html", {"request": request, "meetings": meetings, "active_page": "attendance"})


@router.get("/meetings/{meeting_id}/attendance", response_class=HTMLResponse)
async def get_meeting_attendance_sheet(request: Request, meeting_id: int, user=Depends(get_current_user)):
    """
    Fetches meeting details, separates members and guests into distinct rosters,
    and renders the interactive batch check-in sheet with Present/Absent/Excused statuses.
    """
    meeting = None
    club_members = []
    guests_roster = []

    if supabase:
        try:
            # 1. Fetch meeting info
            m_res = supabase.table("meetings").select("*").eq("id", meeting_id).execute()
            if m_res.data:
                meeting = m_res.data[0]

            # 2. Fetch all members and prospects
            mem_res = supabase.table("members").select("*").order("full_name").execute()
            all_members = mem_res.data or []

            # 3. Fetch existing attendance for this meeting
            att_res = supabase.table("attendance").select("*").eq("meeting_id", meeting_id).execute()
            existing_att = {a["member_id"]: a["status"] for a in (att_res.data or [])}

            # 4. Assemble rosters separately
            for mem in all_members:
                mid = mem["id"]
                recorded_status = existing_att.get(mid)
                
                # Map recorded status: if legacy 'Guest' or missing, default to 'Present'
                if not recorded_status or recorded_status == "Guest":
                    default_status = "Present"
                else:
                    default_status = recorded_status

                entry = {
                    "id": mid,
                    "full_name": mem.get("full_name", ""),
                    "email": mem.get("email", ""),
                    "member_type": mem.get("status", "Active"),
                    "status": default_status
                }

                if mem.get("status") == "Prospect":
                    guests_roster.append(entry)
                else:
                    club_members.append(entry)

        except Exception as e:
            print(f"Error fetching meeting attendance sheet: {e}")

    context = {
        "request": request,
        "meeting": meeting,
        "meeting_id": meeting_id,
        "club_members": club_members,
        "guests_roster": guests_roster,
        "total_people": len(club_members) + len(guests_roster),
        "statuses": ATTENDANCE_STATUSES,
        "active_page": "attendance"
    }
    return templates.TemplateResponse(request, "partials/attendance.html", context)


@router.post("/attendance", response_class=HTMLResponse)
@router.post("/meetings/attendance/save", response_class=HTMLResponse)
async def save_batch_attendance(request: Request, user=Depends(get_current_user)):
    """
    Processes batch attendance submission for a meeting.
    Extracts all 'status_{member_id}' inputs and saves them into the attendance table.
    """
    form_data = await request.form()
    
    meeting_id_raw = form_data.get("meeting_id")
    if not meeting_id_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing meeting_id")

    try:
        meeting_id = int(meeting_id_raw)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid meeting_id")

    allowed_statuses = ATTENDANCE_STATUSES + ["Guest"]
    attendance_records = []
    for key, value in form_data.items():
        if key.startswith("status_"):
            try:
                member_id = int(key.replace("status_", ""))
                status_val = str(value)
                if status_val in allowed_statuses:
                    attendance_records.append({
                        "meeting_id": meeting_id,
                        "member_id": member_id,
                        "status": status_val
                    })
            except ValueError:
                continue

    if supabase and attendance_records:
        try:
            # Delete existing records for this meeting and insert new ones
            supabase.table("attendance").delete().eq("meeting_id", meeting_id).execute()
            supabase.table("attendance").insert(attendance_records).execute()
        except Exception as e:
            print(f"Error saving batch attendance: {e}")

    # Return updated meetings list view with success notification
    meetings = fetch_meetings_with_stats()
    context = {
        "request": request,
        "meetings": meetings,
        "success_message": f"Attendance successfully recorded for Meeting #{meeting_id} ({len(attendance_records)} people logged).",
        "active_page": "attendance"
    }
    return templates.TemplateResponse(request, "partials/meetings.html", context)



@router.get("/meetings/live", response_class=HTMLResponse)
@router.get("/meetings/{meeting_id}/live", response_class=HTMLResponse)
async def get_live_meeting_console(request: Request, meeting_id: int = None, user=Depends(get_current_user)):
    """
    Renders the Live Meeting Console for meeting day operations.
    Loads active meeting, assigned roles & speeches, all meetings for switching, and live attendance metrics.
    """
    meeting = None
    all_meetings = []
    assigned_roles = []
    meeting_guests = []
    attendance_stats = {"present": 0, "absent": 0, "excused": 0, "guest": 0, "total": 0}

    if supabase:
        try:
            # 1. Fetch all meetings for dropdown switcher
            m_res = supabase.table("meetings").select("*").order("meeting_date", desc=True).order("meeting_number", desc=True).execute()
            all_meetings = m_res.data or []

            # 2. Select target meeting
            if meeting_id:
                for m in all_meetings:
                    if m["id"] == meeting_id:
                        meeting = m
                        break
                if not meeting:
                    m_single = supabase.table("meetings").select("*").eq("id", meeting_id).execute()
                    if m_single.data:
                        meeting = m_single.data[0]
            elif all_meetings:
                meeting = all_meetings[0]

            if meeting:
                mid = meeting["id"]

                # 3. Fetch assigned roles
                roles_res = supabase.table("role_assignments").select(
                    "id, speech_title, role_catalog(role_name, category), members(id, full_name, email, status)"
                ).eq("meeting_id", mid).execute()
                assigned_roles = roles_res.data or []

                # 4. Fetch attendance records joined with member status
                att_res = supabase.table("attendance").select(
                    "status, member_id, members(id, full_name, status)"
                ).eq("meeting_id", mid).execute()
                all_att = att_res.data or []

                # 5. Fetch registered prospects/guests in the club
                guests_res = supabase.table("members").select("id, full_name, email, phone").eq("status", "Prospect").order("created_at", desc=True).execute()
                all_prospects = guests_res.data or []

                # Compute attendance breakdown
                for a in all_att:
                    st = a.get("status")
                    mem = a.get("members") or {}
                    is_prospect = mem.get("status") == "Prospect"

                    if is_prospect:
                        if st == "Present" or st == "Guest":
                            attendance_stats["guest"] += 1
                    else:
                        if st == "Present":
                            attendance_stats["present"] += 1
                        elif st == "Absent":
                            attendance_stats["absent"] += 1
                        elif st == "Excused":
                            attendance_stats["excused"] += 1

                    attendance_stats["total"] += 1

                # If no meeting-specific attendance has been logged yet, show total registered club guests
                if attendance_stats["guest"] == 0:
                    attendance_stats["guest"] = len(all_prospects)

                meeting_guests = all_prospects

        except Exception as e:
            print(f"Error fetching live meeting console: {e}")

    context = {
        "request": request,
        "meeting": meeting,
        "all_meetings": all_meetings,
        "assigned_roles": assigned_roles,
        "meeting_guests": meeting_guests,
        "attendance_stats": attendance_stats,
        "active_page": "agenda"
    }
    return templates.TemplateResponse(request, "partials/live_meeting.html", context)
