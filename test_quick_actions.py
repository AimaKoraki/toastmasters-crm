from fastapi.testclient import TestClient
from app.main import app
from app.config import EXCO_PASSKEY

client = TestClient(app)

def login():
    return client.post("/login", data={"passkey": EXCO_PASSKEY}, follow_redirects=False)

def test_quick_actions():
    login()
    
    # 1. Quick Action: Add Guest
    res1 = client.get("/prospects/new")
    assert res1.status_code == 200
    assert "Log New Meeting Guest" in res1.text
    
    # 2. Quick Action: Record Attendance
    res2 = client.get("/meetings/attendance")
    assert res2.status_code == 200
    assert "Attendance Check-in" in res2.text or "Meetings &amp; Attendance" in res2.text
    
    # 3. Quick Action: Assign Roles
    res3 = client.get("/roles/assign")
    assert res3.status_code == 200
    assert "Assign Meeting Role" in res3.text
    
    # 4. Quick Action: Start Meeting (Live Meeting Mode)
    res4 = client.get("/meetings/live")
    assert res4.status_code == 200
    assert "Live Meeting Mode" in res4.text
    
    # 5. Quick Action: Export Report (Modal)
    res5 = client.get("/reports/export")
    assert res5.status_code == 200
    assert "Export Club Reports" in res5.text

def test_reports_page_and_downloads():
    login()
    
    # 1. Reports Overview Dashboard
    res_page = client.get("/reports")
    assert res_page.status_code == 200
    assert "Club Analytics &amp; Reports" in res_page.text or "Club Analytics & Reports" in res_page.text
    
    # 2. Download CSV - Summary
    res_summary = client.get("/reports/download?report_type=summary")
    assert res_summary.status_code == 200
    assert "text/csv" in res_summary.headers.get("content-type", "")
    assert "Active Members" in res_summary.text
    
    # 3. Download CSV - Attendance
    res_att = client.get("/reports/download?report_type=attendance")
    assert res_att.status_code == 200
    assert "text/csv" in res_att.headers.get("content-type", "")
    assert "Meeting #" in res_att.text
    
    # 4. Download CSV - Prospects
    res_prosp = client.get("/reports/download?report_type=prospects")
    assert res_prosp.status_code == 200
    assert "text/csv" in res_prosp.headers.get("content-type", "")
    assert "Latest Stage" in res_prosp.text
    
    # 5. Download CSV - Roles
    res_roles = client.get("/reports/download?report_type=roles")
    assert res_roles.status_code == 200
    assert "text/csv" in res_roles.headers.get("content-type", "")
    assert "Role Name" in res_roles.text

if __name__ == "__main__":
    print("Running dashboard quick actions & reports tests...")
    test_quick_actions()
    print("[PASS] test_quick_actions")
    test_reports_page_and_downloads()
    print("[PASS] test_reports_page_and_downloads")
    print("All quick actions and reports tests passed successfully!")
