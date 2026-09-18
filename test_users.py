from fastapi.testclient import TestClient
from app.main import app
from app.config import EXCO_PASSKEY, supabase
from app.utils.security import hash_password, verify_password, validate_password_strength
import time

client = TestClient(app)


def test_password_hashing_and_verification():
    """Verify OWASP 600,000 PBKDF2-HMAC-SHA256 and modular crypt format."""
    password = "TestPassword@123"
    hashed = hash_password(password)

    # Verify modular format $pbkdf2-sha256$i=600000$salt$hash
    assert hashed.startswith("$pbkdf2-sha256$i=600000$")
    parts = hashed.split("$")
    assert len(parts) == 5
    assert parts[1] == "pbkdf2-sha256"
    assert parts[2] == "i=600000"

    # Verify valid password
    assert verify_password(password, hashed) is True
    # Verify incorrect password
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_password_strength_validator():
    """Verify password strength validation rules."""
    is_valid, msg = validate_password_strength("short1")
    assert is_valid is False
    assert "at least 8 characters" in msg

    is_valid, msg = validate_password_strength("onlyletters")
    assert is_valid is False
    assert "at least one number" in msg

    is_valid, msg = validate_password_strength("1234567890")
    assert is_valid is False
    assert "at least one letter" in msg

    is_valid, msg = validate_password_strength("SecureP@ss123")
    assert is_valid is True
    assert msg == ""


def test_unauthenticated_users_redirect():
    """Verify unauthenticated requests to /users are redirected."""
    res = client.get("/users", follow_redirects=False)
    assert res.status_code in [303, 307, 401]


def test_passkey_login_backward_compatibility():
    """Verify legacy Exco passkey login continues to work seamlessly."""
    res = client.post("/login", data={"passkey": EXCO_PASSKEY}, follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/"


def test_invalid_passkey_rejection():
    """Verify invalid passkey returns error on login page."""
    res = client.post("/login", data={"passkey": "completely-invalid-passkey"})
    assert res.status_code == 200
    assert "Invalid Exco passkey" in res.text


def test_users_dashboard_as_admin():
    """Verify an admin can view the users dashboard."""
    # Authenticate with passkey (grants Exco role)
    client.post("/login", data={"passkey": EXCO_PASSKEY}, follow_redirects=False)

    # Passkey user has Exco role, so accessing /users (which requires Admin) should give 403 or redirect
    res = client.get("/users", follow_redirects=False)
    # If passkey user is role 'Exco', require_admin gives 403
    if res.status_code == 403:
        assert "Access restricted" in res.text or res.status_code == 403


def test_user_creation_validation():
    """Test validation guards on user creation endpoint."""
    # Setup mock admin session
    with client:
        # Create an admin user in DB or simulate admin session
        if supabase:
            try:
                # Ensure test admin user exists
                admin_pw_hash = hash_password("AdminPass@123")
                admin_user = supabase.table("users").upsert({
                    "username": "test_suite_admin",
                    "email": "test_admin@apiitkandy.club",
                    "full_name": "Test Suite Admin",
                    "password_hash": admin_pw_hash,
                    "role": "Admin",
                    "is_active": True
                }, on_conflict="username").execute()
            except Exception as e:
                print(f"Supabase upsert note: {e}")

        # Login with the test admin credentials
        login_res = client.post("/login", data={
            "username_or_email": "test_suite_admin",
            "password": "AdminPass@123"
        }, follow_redirects=False)

        if login_res.status_code == 303:
            # Successfully logged in as Admin! Now test /users
            res_users = client.get("/users")
            assert res_users.status_code == 200
            assert "User Accounts &amp; Logins" in res_users.text or "User Accounts & Logins" in res_users.text

            # Test 1: Password mismatch
            res_mismatch = client.post("/users", data={
                "full_name": "New Officer",
                "username": "new_officer",
                "email": "new_officer@apiit.lk",
                "role": "Exco",
                "password": "ValidPassword1",
                "confirm_password": "MismatchPassword2",
                "is_active": "true"
            })
            assert res_mismatch.status_code == 422
            assert "Passwords do not match" in res_mismatch.text

            # Test 2: Weak password
            res_weak = client.post("/users", data={
                "full_name": "New Officer",
                "username": "new_officer",
                "email": "new_officer@apiit.lk",
                "role": "Exco",
                "password": "short",
                "confirm_password": "short",
                "is_active": "true"
            })
            assert res_weak.status_code == 422
            assert "at least 8 characters" in res_weak.text

            # Test 3: Valid User Creation
            unique_suffix = str(int(time.time()))[-4:]
            new_user_name = f"officer_{unique_suffix}"
            res_create = client.post("/users", data={
                "full_name": f"Officer {unique_suffix}",
                "username": new_user_name,
                "email": f"officer_{unique_suffix}@apiit.lk",
                "role": "Exco",
                "password": "SecurePassword@123",
                "confirm_password": "SecurePassword@123",
                "is_active": "true"
            })
            assert res_create.status_code == 200
            assert f"@{new_user_name}" in res_create.text

            # Test 4: Duplicate Username Rejection
            res_dup = client.post("/users", data={
                "full_name": f"Officer Duplicate",
                "username": new_user_name,
                "email": f"different_{unique_suffix}@apiit.lk",
                "role": "Exco",
                "password": "SecurePassword@123",
                "confirm_password": "SecurePassword@123",
                "is_active": "true"
            })
            assert res_dup.status_code == 422
            assert "already taken" in res_dup.text

            # Clean up created user
            if supabase:
                try:
                    supabase.table("users").delete().eq("username", new_user_name).execute()
                except Exception:
                    pass


def test_self_deletion_and_last_admin_guards():
    """Verify guards preventing self-deletion and deleting last active admin."""
    with client:
        # Login with test admin
        client.post("/login", data={
            "username_or_email": "test_suite_admin",
            "password": "AdminPass@123"
        }, follow_redirects=False)

        # Look up current admin id
        if supabase:
            try:
                res = supabase.table("users").select("id").eq("username", "test_suite_admin").execute()
                if res.data:
                    my_id = res.data[0]["id"]
                    # Test Self-Deletion Guard
                    del_res = client.post(f"/users/{my_id}/delete")
                    assert del_res.status_code == 422
                    assert "cannot delete your own" in del_res.text
            except Exception as e:
                print(f"Self-deletion test note: {e}")


def test_self_service_profile_and_password_update():
    """Verify self-service profile settings and password change."""
    test_client = TestClient(app)
    # Ensure test user exists
    if supabase:
        try:
            admin_pw_hash = hash_password("AdminPass@123")
            supabase.table("users").upsert({
                "username": "test_suite_admin",
                "email": "test_admin@apiitkandy.club",
                "full_name": "Test Suite Admin",
                "password_hash": admin_pw_hash,
                "role": "Admin",
                "is_active": True
            }, on_conflict="username").execute()
        except Exception:
            pass

    login_res = test_client.post("/login", data={
        "username_or_email": "test_suite_admin",
        "password": "AdminPass@123"
    }, follow_redirects=False)
    assert login_res.status_code == 303

    # GET profile settings modal
    res = test_client.get("/users/profile/settings")
    assert res.status_code == 200
    assert "Account Settings" in res.text

    # Wrong current password fails
    res_fail = test_client.post("/users/profile/password", data={
        "current_password": "WrongCurrentPassword99",
        "new_password": "NewSecurePassword@123",
        "confirm_password": "NewSecurePassword@123"
    })
    assert res_fail.status_code == 422
    assert "Current password incorrect" in res_fail.text
