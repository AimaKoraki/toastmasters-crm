import hashlib
import hmac
import secrets
import re

# OWASP / NIST 2024 recommended minimum for PBKDF2-HMAC-SHA256
PBKDF2_ITERATIONS = 600000
KEY_LENGTH = 32  # 256 bits

def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 600,000 iterations.
    Outputs modular crypt format: $pbkdf2-sha256$i=600000$salt_hex$hash_hex
    """
    if not password:
        raise ValueError("Password cannot be empty.")
        
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
        dklen=KEY_LENGTH
    )
    return f"$pbkdf2-sha256$i={PBKDF2_ITERATIONS}${salt}${derived_key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a plain password against the stored modular crypt hash in constant time.
    """
    if not password or not stored_hash:
        return False

    try:
        parts = stored_hash.strip().split("$")
        # Format: ['', 'pbkdf2-sha256', 'i=600000', salt, hash]
        if len(parts) != 5 or parts[1] != "pbkdf2-sha256":
            return False

        iter_part = parts[2]
        if not iter_part.startswith("i="):
            return False
        iterations = int(iter_part.split("=")[1])
        salt = parts[3]
        expected_hash = parts[4]

        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
            dklen=KEY_LENGTH
        )
        return hmac.compare_digest(computed_key.hex(), expected_hash)
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates password strength:
    - Minimum 8 characters
    - Must contain at least one letter and one number
    Returns (is_valid, error_message).
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, ""
