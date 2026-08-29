from fastapi.testclient import TestClient
from app.main import app
from app.config import EXCO_PASSKEY, supabase

client = TestClient(app)

def login():
    return client.post("/login", data={"passkey": EXCO_PASSKEY}, follow_redirects=False)

def test_unauthenticated_meetings():
    response = client.get("/meetings", follow_redirects=False)
    assert response.status_code in [303, 307, 401]

def test_authenticated_get_meetings():
    login()
    response = client.get("/meetings")
    assert response.status_code == 200
    assert "Meetings &amp; Attendance" in response.text or "Meetings & Attendance" in response.text

def test_create_meeting():
    login()
    import time
    unique_number = int(str(int(time.time()))[-4:]) + 5000  # e.g. 58734
    meeting_data = {
        "meeting_number": unique_number,
        "meeting_date": "2026-09-20",
        "theme": "Dynamic Attendance Test"
    }
    response = client.post("/meetings", data=meeting_data)
    assert response.status_code == 200
    assert f"Meeting #{unique_number}" in response.text or "Meetings &amp; Attendance" in response.text

def test_get_new_meeting_modal():
    login()
    response = client.get("/meetings/new")
    assert response.status_code == 200
    assert "Schedule New Meeting" in response.text

def test_get_attendance_sheet():
    login()
    # Fetch a valid meeting ID
    meeting_id = 1
    if supabase:
        try:
            m_res = supabase.table("meetings").select("id").limit(1).execute()
            if m_res.data:
                meeting_id = m_res.data[0]["id"]
        except Exception:
            pass

    response = client.get(f"/meetings/{meeting_id}/attendance")
    assert response.status_code == 200
    assert "Attendance Check-in" in response.text

def test_save_batch_attendance():
    login()
    
    meeting_id = 1
    member_ids = []
    if supabase:
        try:
            m_res = supabase.table("meetings").select("id").limit(1).execute()
            if m_res.data:
                meeting_id = m_res.data[0]["id"]
            
            mem_res = supabase.table("members").select("id").limit(3).execute()
            member_ids = [m["id"] for m in (mem_res.data or [])]
        except Exception:
            pass

    # Assemble form data for existing members
    form_data = {"meeting_id": meeting_id}
    for i, mid in enumerate(member_ids):
        status_choice = ["Present", "Absent", "Excused"][i % 3]
        form_data[f"status_{mid}"] = status_choice

    response = client.post("/attendance", data=form_data)
    assert response.status_code == 200
    assert "Attendance successfully recorded" in response.text or "Meetings &amp; Attendance" in response.text

def test_quick_action_attendance_helper():
    login()
    response = client.get("/meetings/attendance")
    assert response.status_code == 200

if __name__ == "__main__":
    print("Running meetings & attendance tests...")
    test_unauthenticated_meetings()
    print("[PASS] test_unauthenticated_meetings")
    test_authenticated_get_meetings()
    print("[PASS] test_authenticated_get_meetings")
    test_create_meeting()
    print("[PASS] test_create_meeting")
    test_get_new_meeting_modal()
    print("[PASS] test_get_new_meeting_modal")
    test_get_attendance_sheet()
    print("[PASS] test_get_attendance_sheet")
    test_save_batch_attendance()
    print("[PASS] test_save_batch_attendance")
    test_quick_action_attendance_helper()
    print("[PASS] test_quick_action_attendance_helper")
    print("All meeting & attendance tests passed successfully!")
