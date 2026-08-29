from fastapi.testclient import TestClient
from app.main import app
from app.config import EXCO_PASSKEY, supabase

client = TestClient(app)

def login():
    return client.post("/login", data={"passkey": EXCO_PASSKEY}, follow_redirects=False)

def test_unauthenticated_roles():
    response = client.get("/roles", follow_redirects=False)
    assert response.status_code in [303, 307, 401]

def test_authenticated_get_roles():
    login()
    response = client.get("/roles")
    assert response.status_code == 200
    assert "Member Role History Matrix" in response.text

def test_get_roles_by_category():
    login()
    response = client.get("/roles?category=Major")
    assert response.status_code == 200
    assert "Member Role History Matrix" in response.text

def test_get_assign_role_modal():
    login()
    response = client.get("/roles/assign")
    assert response.status_code == 200
    assert "Assign Meeting Role" in response.text

def test_assign_role():
    login()
    
    meeting_id = 1
    member_id = 1
    role_id = 1
    
    if supabase:
        try:
            m_res = supabase.table("meetings").select("id").limit(1).execute()
            if m_res.data:
                meeting_id = m_res.data[0]["id"]
            
            mem_res = supabase.table("members").select("id").limit(1).execute()
            if mem_res.data:
                member_id = mem_res.data[0]["id"]
                
            cat_res = supabase.table("role_catalog").select("id").limit(1).execute()
            if cat_res.data:
                role_id = cat_res.data[0]["id"]
        except Exception:
            pass

    assign_data = {
        "meeting_id": meeting_id,
        "member_id": member_id,
        "role_id": role_id,
        "speech_title": "Icebreaker Speech Test"
    }
    response = client.post("/roles/assign", data=assign_data)
    assert response.status_code == 200
    assert "Role assignment successfully recorded" in response.text or "Member Role History Matrix" in response.text

def test_member_role_history():
    login()
    member_id = 1
    if supabase:
        try:
            mem_res = supabase.table("members").select("id").limit(1).execute()
            if mem_res.data:
                member_id = mem_res.data[0]["id"]
        except Exception:
            pass

    response = client.get(f"/roles/member/{member_id}/history")
    assert response.status_code == 200

if __name__ == "__main__":
    print("Running role matrix & assignments tests...")
    test_unauthenticated_roles()
    print("[PASS] test_unauthenticated_roles")
    test_authenticated_get_roles()
    print("[PASS] test_authenticated_get_roles")
    test_get_roles_by_category()
    print("[PASS] test_get_roles_by_category")
    test_get_assign_role_modal()
    print("[PASS] test_get_assign_role_modal")
    test_assign_role()
    print("[PASS] test_assign_role")
    test_member_role_history()
    print("[PASS] test_member_role_history")
    print("All role matrix tests passed successfully!")
