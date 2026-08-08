import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api import network_access  # noqa: E402


class FakeRequest:
    def __init__(self, cloudflare_ip=None, client_ip=None):
        self.headers = {}
        if cloudflare_ip is not None:
            self.headers["CF-Connecting-IP"] = cloudflare_ip
        self.client = (
            SimpleNamespace(host=client_ip)
            if client_ip is not None
            else None
        )


class PrivilegedIpRestrictionTests(unittest.TestCase):
    def test_student_unrestricted(self):
        request = FakeRequest(cloudflare_ip="203.0.113.50")
        with patch.object(network_access, "ADMIN_ALLOWED_NETWORKS", ("187.120.34.90",)):
            network_access.require_role_network_access("student", request)

    def test_coach_ipv4_allowed(self):
        request = FakeRequest(cloudflare_ip="187.120.34.90")
        with patch.object(
            network_access,
            "ADMIN_ALLOWED_NETWORKS",
            ("187.120.34.90", "187.120.36.36"),
        ):
            network_access.require_role_network_access("coach", request)

    def test_master_ipv6_prefix_allowed(self):
        request = FakeRequest(
            cloudflare_ip="2804:104:4107:a1d1:a914:4308:184d:5448"
        )
        with patch.object(
            network_access,
            "ADMIN_ALLOWED_NETWORKS",
            ("2804:104:4107:a1d1::/64",),
        ):
            network_access.require_role_network_access("master", request)

    def test_admin_outside_denied(self):
        request = FakeRequest(cloudflare_ip="203.0.113.50")
        with patch.object(
            network_access,
            "ADMIN_ALLOWED_NETWORKS",
            (
                "187.120.34.90",
                "187.120.36.36",
                "2804:104:4107:a1d1::/64",
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                network_access.require_role_network_access("admin", request)
        self.assertEqual(raised.exception.status_code, 403)

    def test_cf_header_priority(self):
        request = FakeRequest(
            cloudflare_ip="203.0.113.50",
            client_ip="187.120.34.90",
        )
        self.assertEqual(
            network_access.client_ip_from_request(request),
            "203.0.113.50",
        )

    def test_empty_configuration_disables_restriction(self):
        request = FakeRequest(cloudflare_ip="203.0.113.50")
        with patch.object(network_access, "ADMIN_ALLOWED_NETWORKS", ()):
            network_access.require_role_network_access("coach", request)


if __name__ == "__main__":
    unittest.main()
