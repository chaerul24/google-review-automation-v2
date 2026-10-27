import json
import os
import unittest
from dotenv import load_dotenv

load_dotenv()

import app
import db


class ReactApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        db.migrate_autobotix()
        cls.password = os.environ.get("APP_PASSWORD") or "development-only-password"

    def client(self):
        return app.app.test_client()

    def auth_client(self):
        c = self.client()
        res = c.post("/api/login", json={"password": self.password})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("authenticated"))
        self.token = data.get("csrf_token")
        return c

    def test_anonymous_auth_me_returns_unauthenticated(self):
        c = self.client()
        res = c.get("/api/auth/me")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data.get("authenticated"))
        self.assertTrue(bool(data.get("csrf_token")))

    def test_spa_index_served_on_root_for_anonymous(self):
        c = self.client()
        res = c.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'<div id="root"></div>', res.data)
        self.assertIn(b"AutoBotix", res.data)

    def test_login_invalid_password(self):
        c = self.client()
        res = c.post("/api/login", json={"password": "wrong-password-12345"})
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")

    def test_login_and_auth_me_lifecycle(self):
        c = self.client()
        res = c.post("/api/login", json={"password": self.password})
        self.assertEqual(res.status_code, 200)
        token = res.get_json().get("csrf_token")

        me = c.get("/api/auth/me").get_json()
        self.assertTrue(me.get("authenticated"))
        self.assertEqual(me.get("role"), "administrator")

        logout = c.post("/api/logout", headers={"X-CSRF-Token": token})
        self.assertEqual(logout.status_code, 200)

        me_after = c.get("/api/auth/me").get_json()
        self.assertFalse(me_after.get("authenticated"))

    def test_protected_api_rejects_unauthenticated(self):
        c = self.client()
        res = c.get("/api/dashboard")
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data.get("authenticated"))

    def test_authenticated_dashboard_api(self):
        c = self.auth_client()
        res = c.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("businesses", data)
        self.assertIn("all_emails", data)
        self.assertIn("all_cookies", data)
        self.assertIn("queue_metrics", data)
        self.assertIn("inventory", data)
        self.assertIn("host_metrics", data)

    def test_authenticated_autobotix_apis(self):
        c = self.auth_client()
        overview = c.get("/api/autobotix/overview")
        self.assertEqual(overview.status_code, 200)
        self.assertIn("domain_count", overview.get_json())

        domains = c.get("/api/autobotix/domains")
        self.assertEqual(domains.status_code, 200)
        self.assertIn("domains", domains.get_json())

        tunnels = c.get("/api/autobotix/tunnels")
        self.assertEqual(tunnels.status_code, 200)
        self.assertIn("tunnels", tunnels.get_json())

        monitoring = c.get("/api/autobotix/monitoring")
        self.assertEqual(monitoring.status_code, 200)
        self.assertIn("metrics", monitoring.get_json())

        activity = c.get("/api/autobotix/activity")
        self.assertEqual(activity.status_code, 200)
        self.assertIn("logs", activity.get_json())

    def test_business_crud_api(self):
        c = self.auth_client()
        headers = {"X-CSRF-Token": self.token}

        # Add business
        add_res = c.post("/api/businesses", json={
            "name": "Test React Business",
            "url": "https://maps.google.com/?cid=99999999",
        }, headers=headers)
        self.assertEqual(add_res.status_code, 200)
        biz_id = add_res.get_json().get("business_id")
        self.assertTrue(biz_id > 0)

        # Get business detail
        detail_res = c.get(f"/api/businesses/{biz_id}")
        self.assertEqual(detail_res.status_code, 200)
        biz_data = detail_res.get_json()
        self.assertEqual(biz_data["business"]["name"], "Test React Business")

        # Save config
        config_res = c.post(f"/api/businesses/{biz_id}/config", json={
            "business_description": "A very friendly restaurant",
            "review_style": "casual",
            "star_5_count": 5,
            "delay_seconds": 30,
        }, headers=headers)
        self.assertEqual(config_res.status_code, 200)

        # Delete business
        del_res = c.delete(f"/api/businesses/{biz_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)

        # Verify 404
        after_del = c.get(f"/api/businesses/{biz_id}")
        self.assertEqual(after_del.status_code, 404)


if __name__ == "__main__":
    unittest.main()
