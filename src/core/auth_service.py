import base64
import hashlib
import hmac
import json
import os
import secrets
import time


class AuthService:

    _secret = os.getenv("AUTH_SECRET", "runcore-local-development-secret")

    @staticmethod
    def hash_password(password):
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
        return f"scrypt${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_password(password, password_hash):
        try:
            _, salt, digest = password_hash.split("$")
            candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
            return hmac.compare_digest(candidate, digest)
        except ValueError:
            return False

    @classmethod
    def create_token(cls, user_id):
        encoded = base64.urlsafe_b64encode(json.dumps({"sub": user_id, "exp": int(time.time()) + 28800}).encode()).decode().rstrip("=")
        signature = hmac.new(cls._secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        return f"{encoded}.{signature}"

    @classmethod
    def read_token(cls, token):
        try:
            encoded, signature = token.split(".")
            expected = hmac.new(cls._secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
            payload = json.loads(base64.urlsafe_b64decode(encoded + "==").decode())
            return payload if hmac.compare_digest(signature, expected) and payload["exp"] > time.time() else None
        except (KeyError, ValueError, json.JSONDecodeError):
            return None
