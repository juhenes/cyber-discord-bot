import base64
import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Generate a PBKDF2-SHA256 password hash with a random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    encode = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"{_ALGORITHM}${_ITERATIONS}${encode(salt)}${encode(digest)}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a plaintext password against an encoded PBKDF2-SHA256 hash."""
    try:
        algorithm, iterations, encoded_salt, encoded_digest = encoded_hash.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        salt = base64.urlsafe_b64decode(encoded_salt + "===")
        expected = base64.urlsafe_b64decode(encoded_digest + "===")
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)
