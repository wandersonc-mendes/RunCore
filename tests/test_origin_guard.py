import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api import origin_guard


class FakeRequest:
    def __init__(self, path="/api/auth/login", secret=None):
        self.url = SimpleNamespace(path=path)
        self.headers = {}
        if secret is not None:
            self.headers[origin_guard.ORIGIN_SECRET_HEADER] = secret


class OriginGuardTests(unittest.TestCase):
    def test_disabled_when_secret_empty(self):
        request = FakeRequest()
        with patch.object(origin_guard, "CLOUDFLARE_ORIGIN_SECRET", ""):
            self.assertTrue(origin_guard.origin_request_is_allowed(request))

    def test_health_always_allowed(self):
        request = FakeRequest(path="/health")
        with patch.object(origin_guard, "CLOUDFLARE_ORIGIN_SECRET", "server-secret"):
            self.assertTrue(origin_guard.origin_request_is_allowed(request))

    def test_correct_secret_allowed(self):
        request = FakeRequest(secret="server-secret")
        with patch.object(origin_guard, "CLOUDFLARE_ORIGIN_SECRET", "server-secret"):
            self.assertTrue(origin_guard.origin_request_is_allowed(request))

    def test_missing_secret_denied(self):
        request = FakeRequest()
        with patch.object(origin_guard, "CLOUDFLARE_ORIGIN_SECRET", "server-secret"):
            self.assertFalse(origin_guard.origin_request_is_allowed(request))

    def test_wrong_secret_denied(self):
        request = FakeRequest(secret="wrong-secret")
        with patch.object(origin_guard, "CLOUDFLARE_ORIGIN_SECRET", "server-secret"):
            self.assertFalse(origin_guard.origin_request_is_allowed(request))


if __name__ == "__main__":
    unittest.main()
