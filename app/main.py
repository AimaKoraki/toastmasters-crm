from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth, prospects, meetings, roles
from app.dependencies import get_current_user
from fastapi import Depends

app = FastAPI(title="Club CRM")

# Add Session Middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-exco-key")

# Static and Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include Routers
app.include_router(auth.router)
app.include_router(prospects.router)
app.include_router(meetings.router)
app.include_router(roles.router)

@app.get("/")
def read_root(request: Request, user=Depends(get_current_user)):
    # Initialize variables with defaults
    members_count = 0
    guests_count = 0
    prospects_count = 0
    attendance_rate = 0
    upcoming_meeting = None
    recent_activities = []
    pipeline_data = []
    
    from app.config import supabase
    from datetime import datetime
    
    def parse_time(dt_str):
        if not dt_str: return datetime.min
        # Handle ISO format from Supabase
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return datetime.min
            
    if supabase:
        # 1. Stat Counters
        try:
            m_res = supabase.table("members").select("id", count="exact").eq("status", "Active").execute()
            members_count = m_res.count if m_res.count is not None else 0
        except Exception:
            pass

        try:
            g_res = supabase.table("members").select("id", count="exact").eq("status", "Prospect").execute()
            guests_count = g_res.count if g_res.count is not None else 0
        except Exception:
            pass
            
        try:
            logs_res = supabase.table("prospect_logs").select("member_id, stage, created_at").order("created_at", desc=True).execute()
            latest_stages = {}
            for log in logs_res.data:
                mid = log["member_id"]
                if mid not in latest_stages:
                    latest_stages[mid] = log["stage"]
            prospects_count = sum(1 for stage in latest_stages.values() if stage != 'Onboarded')
        except Exception:
            latest_stages = {}
            
        try:
            att_res = supabase.table("attendance").select("status").execute()
            att_records = [a for a in att_res.data if a["status"] in ["Present", "Absent", "Excused"]]
            total_member_meetings = len(att_records)
            if total_member_meetings > 0:
                total_present = sum(1 for a in att_records if a["status"] == "Present")
                attendance_rate = int((total_present / total_member_meetings) * 100)
        except Exception:
            pass
            
        # 2. Upcoming Meeting
        try:
            meetings_res = supabase.table("meetings").select("*").order("meeting_date", desc=True).limit(1).execute()
            if meetings_res.data:
                upcoming_meeting = meetings_res.data[0]
                upcoming_meeting["venue"] = "APIIT Kandy Campus"
                upcoming_meeting["host"] = "TBD"
                
                # Fetch Host
                roles_res = supabase.table("role_assignments").select("member_id, role_catalog(role_name), members(full_name)").eq("meeting_id", upcoming_meeting["id"]).execute()
                for r in roles_res.data:
                    role_cat = r.get("role_catalog")
                    if role_cat and role_cat.get("role_name") == "Meeting Host":
                        mem = r.get("members")
                        if mem:
                            upcoming_meeting["host"] = mem.get("full_name", "TBD")
                        break
        except Exception:
            pass
            
        # 3. Recent Activity Stream
        try:
            pl_res = supabase.table("prospect_logs").select("created_at, stage, members(full_name)").order("created_at", desc=True).limit(5).execute()
            for pl in pl_res.data:
                name = pl.get("members", {}).get("full_name", "Unknown") if pl.get("members") else "Unknown"
                text = f"Guest Registered: {name}" if pl["stage"] == "1st Visit" else f"Prospect Stage Updated: {name} ({pl['stage']})"
                recent_activities.append({
                    "timestamp": pl["created_at"],
                    "parsed_time": parse_time(pl["created_at"]),
                    "text": text
                })
                
            att_recent = supabase.table("attendance").select("created_at, status, meetings(meeting_number), members(full_name)").order("created_at", desc=True).limit(5).execute()
            for att in att_recent.data:
                name = att.get("members", {}).get("full_name", "Unknown") if att.get("members") else "Unknown"
                meeting_num = att.get("meetings", {}).get("meeting_number", "?") if att.get("meetings") else "?"
                recent_activities.append({
                    "timestamp": att["created_at"],
                    "parsed_time": parse_time(att["created_at"]),
                    "text": f"Attendance Recorded: {name} (Meeting #{meeting_num})"
                })
                
            roles_recent = supabase.table("role_assignments").select("created_at, role_catalog(role_name), members(full_name)").order("created_at", desc=True).limit(5).execute()
            for r in roles_recent.data:
                name = r.get("members", {}).get("full_name", "Unknown") if r.get("members") else "Unknown"
                role_name = r.get("role_catalog", {}).get("role_name", "Role") if r.get("role_catalog") else "Role"
                recent_activities.append({
                    "timestamp": r["created_at"],
                    "parsed_time": parse_time(r["created_at"]),
                    "text": f"Role Assigned: {role_name} to {name}"
                })
                
            recent_activities.sort(key=lambda x: x["parsed_time"], reverse=True)
            recent_activities = recent_activities[:5]
        except Exception:
            pass
            
        # 4. Guest Pipeline Table Data
        try:
            prospects_res = supabase.table("members").select("*").eq("status", "Prospect").execute()
            for p in prospects_res.data:
                stage = latest_stages.get(p["id"], "1st Visit")
                if stage != 'Onboarded':
                    pipeline_data.append({
                        "full_name": p["full_name"],
                        "email": p["email"],
                        "phone": p.get("phone", ""),
                        "stage": stage,
                        "created_at": p.get("created_at", "")
                    })
        except Exception:
            pass

    context = {
        "request": request,
        "active_page": "dashboard",
        "members_count": members_count,
        "guests_count": guests_count,
        "prospects_count": prospects_count,
        "attendance_rate": attendance_rate,
        "upcoming_meeting": upcoming_meeting,
        "recent_activities": recent_activities,
        "pipeline_data": pipeline_data
    }
    return templates.TemplateResponse(request, "index.html", context)
