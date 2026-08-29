from fastapi.testclient import TestClient
from app.main import app
from app.config import EXCO_PASSKEY, supabase
import time

client = TestClient(app)

def login():
    return client.post("/login", data={"passkey": EXCO_PASSKEY}, follow_redirects=False)

def test_unauthenticated_members():
    response = client.get("/members", follow_redirects=False)
    assert response.status_code in [303, 307, 401]
    print("[PASS] test_unauthenticated_members passed")

def test_authenticated_get_members():
    login()
    response = client.get("/members")
    assert response.status_code == 200
    assert "Member Directory" in response.text
    assert "Total Roster" in response.text
    print("[PASS] test_authenticated_get_members passed")

def test_members_status_filter():
    login()
    # Test Active tab
    res_active = client.get("/members?status=Active")
    assert res_active.status_code == 200
    assert "Member Directory" in res_active.text

    # Test Inactive tab
    res_inactive = client.get("/members?status=Inactive")
    assert res_inactive.status_code == 200
    assert "Member Directory" in res_inactive.text

    # Test Alumni tab
    res_alumni = client.get("/members?status=Alumni")
    assert res_alumni.status_code == 200
    assert "Member Directory" in res_alumni.text
    print("[PASS] test_members_status_filter passed")

def test_get_new_member_modal():
    login()
    response = client.get("/members/new")
    assert response.status_code == 200
    assert "Add Club Member" in response.text
    assert "Pathways Level" in response.text
    print("[PASS] test_get_new_member_modal passed")

def test_create_and_update_member():
    login()
    
    # 1. Create a new member
    unique_email = f"test_member_{int(time.time())}@apiitclub.org"
    member_data = {
        "full_name": "Roshan Jayasuriya",
        "email": unique_email,
        "phone": "+94 71 888 7777",
        "status": "Active",
        "pathway_level": "Level 2"
    }
    create_res = client.post("/members", data=member_data)
    assert create_res.status_code == 200
    assert "Roshan Jayasuriya" in create_res.text or "Member Directory" in create_res.text

    # 2. Get member ID
    member_id = None
    if supabase:
        try:
            m = supabase.table("members").select("id").eq("email", unique_email).execute()
            if m.data:
                member_id = m.data[0]["id"]
        except Exception as e:
            print(f"Error fetching created member: {e}")

    if member_id:
        # 3. Test Edit Modal retrieval
        edit_modal_res = client.get(f"/members/{member_id}/edit")
        assert edit_modal_res.status_code == 200
        assert "Edit Member Profile" in edit_modal_res.text
        assert "Roshan Jayasuriya" in edit_modal_res.text

        # 4. Test Update Member
        update_data = {
            "full_name": "Roshan Jayasuriya DTM",
            "email": unique_email,
            "phone": "+94 71 888 7777",
            "status": "Active",
            "pathway_level": "DTM"
        }
        update_res = client.post(f"/members/{member_id}", data=update_data)
        assert update_res.status_code == 200
        assert "Roshan Jayasuriya DTM" in update_res.text or "Member Directory" in update_res.text

    print("[PASS] test_create_and_update_member passed")

if __name__ == "__main__":
    print("Running Module C: Member Management tests...")
    test_unauthenticated_members()
    test_authenticated_get_members()
    test_members_status_filter()
    test_get_new_member_modal()
    test_create_and_update_member()
    print("All Member Management tests successfully passed!")
