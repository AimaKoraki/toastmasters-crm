import csv
import io
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from ..config import supabase
from ..dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse)
async def get_reports_page(request: Request, user=Depends(get_current_user)):
    """
    Renders the Reports overview page with KPI summaries and export cards.
    """
    total_members = 0
    total_guests = 0
    total_meetings = 0
    total_attendance = 0

    if supabase:
        try:
            m_res = supabase.table("members").select("id", count="exact").eq("status", "Active").execute()
            total_members = m_res.count or 0

            g_res = supabase.table("members").select("id", count="exact").eq("status", "Prospect").execute()
            total_guests = g_res.count or 0

            meet_res = supabase.table("meetings").select("id", count="exact").execute()
            total_meetings = meet_res.count or 0

            att_res = supabase.table("attendance").select("id", count="exact").execute()
            total_attendance = att_res.count or 0
        except Exception as e:
            print(f"Error fetching report stats: {e}")

    context = {
        "request": request,
        "total_members": total_members,
        "total_guests": total_guests,
        "total_meetings": total_meetings,
        "total_attendance": total_attendance,
        "active_page": "reports"
    }
    return templates.TemplateResponse(request, "partials/reports.html", context)


@router.get("/export", response_class=HTMLResponse)
async def get_export_modal(request: Request, user=Depends(get_current_user)):
    """
    Returns standalone Export Report modal for dashboard quick action.
    """
    return templates.TemplateResponse(request, "partials/export_modal.html", {"request": request})


@router.get("/download")
async def download_csv_report(report_type: str = "summary", user=Depends(get_current_user)):
    """
    Streams CSV export file based on requested report_type.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    if report_type == "prospects":
        filename = f"club_guests_pipeline_{now_str}.csv"
        writer.writerow(["ID", "Full Name", "Email", "Phone", "Status", "Latest Stage", "Latest Notes", "Created At"])
        
        if supabase:
            try:
                m_res = supabase.table("members").select("*").eq("status", "Prospect").order("created_at", desc=True).execute()
                prospects = m_res.data or []

                l_res = supabase.table("prospect_logs").select("*").order("created_at", desc=True).execute()
                all_logs = l_res.data or []
                
                latest_logs = {}
                for log in all_logs:
                    mid = log["member_id"]
                    if mid not in latest_logs:
                        latest_logs[mid] = log

                for p in prospects:
                    pid = p["id"]
                    l = latest_logs.get(pid, {})
                    writer.writerow([
                        p.get("id"),
                        p.get("full_name"),
                        p.get("email"),
                        p.get("phone", ""),
                        p.get("status"),
                        l.get("stage", "1st Visit"),
                        l.get("notes", ""),
                        p.get("created_at")
                    ])
            except Exception as e:
                print(f"Error exporting prospects CSV: {e}")

    elif report_type == "attendance":
        filename = f"club_attendance_logs_{now_str}.csv"
        writer.writerow(["Meeting #", "Meeting Date", "Meeting Theme", "Member Name", "Email", "Attendance Status"])
        
        if supabase:
            try:
                att_res = supabase.table("attendance").select(
                    "status, meetings(meeting_number, meeting_date, theme), members(full_name, email)"
                ).execute()
                
                for a in (att_res.data or []):
                    m = a.get("meetings") or {}
                    mem = a.get("members") or {}
                    writer.writerow([
                        m.get("meeting_number", ""),
                        m.get("meeting_date", ""),
                        m.get("theme", ""),
                        mem.get("full_name", ""),
                        mem.get("email", ""),
                        a.get("status", "")
                    ])
            except Exception as e:
                print(f"Error exporting attendance CSV: {e}")

    elif report_type == "roles":
        filename = f"club_role_assignments_{now_str}.csv"
        writer.writerow(["Meeting #", "Meeting Date", "Role Name", "Category", "Member Name", "Speech Title"])
        
        if supabase:
            try:
                r_res = supabase.table("role_assignments").select(
                    "speech_title, meetings(meeting_number, meeting_date), role_catalog(role_name, category), members(full_name)"
                ).execute()

                for r in (r_res.data or []):
                    m = r.get("meetings") or {}
                    rc = r.get("role_catalog") or {}
                    mem = r.get("members") or {}
                    writer.writerow([
                        m.get("meeting_number", ""),
                        m.get("meeting_date", ""),
                        rc.get("role_name", ""),
                        rc.get("category", ""),
                        mem.get("full_name", ""),
                        r.get("speech_title", "")
                    ])
            except Exception as e:
                print(f"Error exporting roles CSV: {e}")

    else:
        # Summary report
        filename = f"club_crm_summary_{now_str}.csv"
        writer.writerow(["Metric", "Value"])
        if supabase:
            try:
                m_count = supabase.table("members").select("id", count="exact").eq("status", "Active").execute().count or 0
                g_count = supabase.table("members").select("id", count="exact").eq("status", "Prospect").execute().count or 0
                meet_count = supabase.table("meetings").select("id", count="exact").execute().count or 0
                att_count = supabase.table("attendance").select("id", count="exact").execute().count or 0
                roles_count = supabase.table("role_assignments").select("id", count="exact").execute().count or 0

                writer.writerow(["Active Members", m_count])
                writer.writerow(["Total Prospects & Guests", g_count])
                writer.writerow(["Meetings Scheduled", meet_count])
                writer.writerow(["Total Attendance Logged", att_count])
                writer.writerow(["Total Roles Assigned", roles_count])
            except Exception as e:
                print(f"Error exporting summary CSV: {e}")
        else:
            writer.writerow(["Active Members", 0])
            writer.writerow(["Total Prospects & Guests", 0])
            writer.writerow(["Meetings Scheduled", 0])
            writer.writerow(["Total Attendance Logged", 0])
            writer.writerow(["Total Roles Assigned", 0])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
