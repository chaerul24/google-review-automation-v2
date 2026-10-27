import re
import unittest
from pathlib import Path

import app
import db
import domain_intelligence


class AutoBotixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        domain_intelligence.import_historical_snapshot()

    def client(self):
        client = app.app.test_client()
        with client.session_transaction() as session:
            session["logged_in"] = True
            session["csrf_token"] = "test-csrf-token"
        return client

    def test_snapshot_is_idempotent_and_classified(self):
        domain_intelligence.import_historical_snapshot()
        rows = db.get_autobotix_domains()
        self.assertEqual(len(rows), 28)
        self.assertEqual(sum(r["upstream_status"] == "healthy" for r in rows), 20)
        self.assertEqual(sum(r["upstream_status"] == "responding_health_unverified" for r in rows), 4)
        self.assertEqual(sum(r["upstream_status"] == "unreachable" for r in rows), 4)

    def test_csrf_rejects_missing_and_accepts_valid(self):
        client = self.client()
        self.assertEqual(client.post("/autobotix/import-snapshot").status_code, 400)
        self.assertEqual(client.post("/autobotix/import-snapshot", headers={"X-CSRF-Token": "test-csrf-token"}).status_code, 200)

    def test_admin_pages_require_login(self):
        anonymous = app.app.test_client()
        self.assertEqual(anonymous.get("/autobotix/domains").status_code, 302)
        client = self.client()
        for path in ("/autobotix", "/autobotix/domains", "/autobotix/tunnels", "/autobotix/monitoring", "/autobotix/activity"):
            self.assertEqual(client.get(path).status_code, 200, path)

    def test_allow_list_blocks_nonverified_target(self):
        self.assertTrue(domain_intelligence.allowed_target("127.0.0.1", 8000))
        self.assertFalse(domain_intelligence.allowed_target("169.254.169.254", 80))
        self.assertEqual(domain_intelligence.tcp_probe("169.254.169.254", 80)["status"], "blocked")

    def test_sanitizer(self):
        value = domain_intelligence.sanitize("token=abc password=def normal")
        self.assertNotIn("abc", value)
        self.assertNotIn("def", value)

    def test_theme_assets_define_all_modes_and_csrf_fetch_header(self):
        root = Path(__file__).resolve().parent
        css = (root / "static" / "autobotix.css").read_text()
        script = (root / "static" / "autobotix.js").read_text()
        self.assertIn('[data-theme="dark"]', css)
        self.assertIn("autobotix-theme", script)
        self.assertIn("X-CSRF-Token", script)


if __name__ == "__main__":
    unittest.main()
