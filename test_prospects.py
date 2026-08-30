from fastapi.testclient import TestClient
from app.main import app
from app.config import EXCO_PASSKEY

client = TestClient(app)

def login():
    # Helper to authenticate session
    return client.post("/login", data={"passkey": EXCO_PASSKEY}, follow_redirects=False)

def test_unauthenticated_prospects():
    response = client.get("/prospects", follow_redirects=False)
    assert response.status_code in [303, 307, 401]

def test_authenticated_get_prospects():
    # Login first
    login_res = login()
    assert login_res.status_code == 303

    response = client.get("/prospects")
    assert response.status_code == 200
    assert "Guest &amp; Prospect Pipeline" in response.text or "Guest & Prospect Pipeline" in response.text
    assert "1st Visit" in response.text

def test_get_new_prospect_modal():
    login()
    response = client.get("/prospects/new")
    assert response.status_code == 200
    assert "Log New Meeting Guest" in response.text
    assert "Full Name" in response.text

def test_add_prospect_and_stage_progression():
    login()
    
    # 1. Add new guest
    import time
    unique_email = f"test_prospect_{int(time.time())}@example.com"
    guest_data = {
        "full_name": "Test Prospect User",
        "email": unique_email,
        "phone": "+94 77 999 8888",
        "notes": "First time visitor test",
        "initial_stage": "1st Visit"
    }
    add_res = client.post("/prospects", data=guest_data)
    assert add_res.status_code == 200
    assert "Test Prospect User" in add_res.text or "Guest &" in add_res.text

    # 2. Test invalid stage transition
    invalid_res = client.post("/prospects/1/stage", data={"stage": "InvalidStage", "notes": "test"})
    assert invalid_res.status_code == 400

    # 3. Test valid stage update
    stage_res = client.post("/prospects/1/stage", data={"stage": "2nd Visit", "notes": "Attended second meeting"})
    assert stage_res.status_code == 200

    # 4. Test stage update to Onboarded
    onboard_res = client.post("/prospects/1/stage", data={"stage": "Onboarded", "notes": "Paid dues"})
    assert onboard_res.status_code == 200

    # 5. Test get history
    hist_res = client.get("/prospects/1/history")
    assert hist_res.status_code == 200

def test_edit_prospect():
    login()
    # Test edit modal load
    edit_modal_res = client.get("/prospects/1/edit")
    assert edit_modal_res.status_code == 200
    assert "Edit Guest Details" in edit_modal_res.text

    # Test update prospect details
    update_res = client.post("/prospects/1", data={
        "full_name": "Updated Prospect Name",
        "email": "updated_prospect@example.com",
        "phone": "+94 77 111 2222"
    })
    assert update_res.status_code == 200
    assert "successfully updated" in update_res.text or "Updated Prospect Name" in update_res.text

if __name__ == "__main__":
    print("Running tests manually...")
    test_unauthenticated_prospects()
    print("[PASS] test_unauthenticated_prospects passed")
    test_authenticated_get_prospects()
    print("[PASS] test_authenticated_get_prospects passed")
    test_get_new_prospect_modal()
    print("[PASS] test_get_new_prospect_modal passed")
    test_add_prospect_and_stage_progression()
    print("[PASS] test_add_prospect_and_stage_progression passed")
    test_edit_prospect()
    print("[PASS] test_edit_prospect passed")
    print("All tests successfully passed!")

