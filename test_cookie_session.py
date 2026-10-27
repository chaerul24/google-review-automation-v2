"""Comprehensive tests for Cookie-Based Chromium Session Manager (AutoBotix).

Tests cover:
- Cookie valid: sesi dapat dipulihkan.
- Cookie kedaluwarsa: status expired.
- Cookie tidak cocok dengan domain: error domain mismatch.
- Cookie rusak / malformed: ditangani aman tanpa membuat worker crash.
- Profil terkunci: pencegahan concurrent profile access via ProfileLock.
- Browser direstart: persistensi sesi Chromium pada profil persisten.
- Non-destruktif: tidak menghapus cookie lama saat kegagalan.
- Sanitasi: tidak membocorkan nilai cookie atau token dalam log/metadata.
"""

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import db
import session_manager
from session_manager import (
    CookieValidationResult,
    ProfileLock,
    ProfileLockedError,
    SessionManager,
    SessionStatus,
    domain_matches,
    extract_domain,
    get_profile_dir,
    validate_cookie_payload,
)


class CookieSessionTests(unittest.TestCase):
    def setUp(self):
        db.init_db()
        db.migrate_add_cookies_table()
        db.migrate_add_cookie_session_columns()
        self.test_email = "autobotix_test_user@autobotix.my.id"

    def tearDown(self):
        # Clean up test email from db
        with db.get_db() as conn:
            conn.execute("DELETE FROM cookies WHERE email = ?", (self.test_email,))
            conn.execute("DELETE FROM emails WHERE email = ?", (self.test_email,))

    def test_domain_matching_logic(self):
        """Test domain matching against target domains."""
        self.assertTrue(domain_matches("autobotix.my.id", "autobotix.my.id"))
        self.assertTrue(domain_matches(".autobotix.my.id", "autobotix.my.id"))
        self.assertTrue(domain_matches("sub.autobotix.my.id", "autobotix.my.id"))
        self.assertTrue(domain_matches(".google.com", "google.com"))
        self.assertTrue(domain_matches(".google.com", "maps.google.com"))
        self.assertFalse(domain_matches("facebook.com", "autobotix.my.id"))
        self.assertFalse(domain_matches("google.com", "autobotix.my.id"))

    def test_valid_cookie_structure_and_sanitization(self):
        """Test that valid cookies parse properly and secrets are never emitted in metadata."""
        future_time = time.time() + 86400  # 1 day in future
        raw_cookies = [
            {
                "name": "session_id",
                "value": "super_secret_session_token_12345",
                "domain": "autobotix.my.id",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "Lax",
                "expirationDate": future_time,
            },
            {
                "name": "user_pref",
                "value": "dark_mode_theme",
                "domain": ".autobotix.my.id",
                "path": "/",
                "secure": False,
                "httpOnly": False,
            },
        ]
        res = validate_cookie_payload(raw_cookies, target_domain="autobotix.my.id")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, SessionStatus.ACTIVE)
        self.assertEqual(res.cookie_count, 2)
        self.assertEqual(res.cookie_names, ["session_id", "user_pref"])

        # Crucial security verification: metadata to_dict must NEVER contain secret token
        summary = res.to_dict()
        summary_str = json.dumps(summary)
        self.assertNotIn("super_secret_session_token_12345", summary_str)
        self.assertNotIn("dark_mode_theme", summary_str)

    def test_expired_cookie_detected(self):
        """Test that expired cookies are detected and return EXPIRED status."""
        past_time = time.time() - 3600  # 1 hour ago
        raw_cookies = [
            {
                "name": "session_token",
                "value": "expired_secret_val",
                "domain": "autobotix.my.id",
                "path": "/",
                "expirationDate": past_time,
            }
        ]
        res = validate_cookie_payload(raw_cookies, target_domain="autobotix.my.id")
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, SessionStatus.EXPIRED)
        self.assertIn("kedaluwarsa", res.reason.lower())

    def test_domain_mismatch_detected(self):
        """Test that cookies for an unrelated domain are flagged as DOMAIN_MISMATCH."""
        future_time = time.time() + 86400
        raw_cookies = [
            {
                "name": "auth_token",
                "value": "secret_abc",
                "domain": "another-unrelated-site.org",
                "path": "/",
                "expirationDate": future_time,
            }
        ]
        res = validate_cookie_payload(raw_cookies, target_domain="autobotix.my.id")
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, SessionStatus.DOMAIN_MISMATCH)
        self.assertIn("autobotix.my.id", res.reason)

    def test_corrupted_cookie_does_not_crash_worker(self):
        """Test that corrupted JSON or non-dict cookie payload does not crash."""
        corrupted_inputs = [
            "{broken json string",
            "",
            "[]",
            json.dumps([{"no_name_field": "val"}]),
            json.dumps([{"name": "test", "value": None}]),
            json.dumps("string_instead_of_list"),
            json.dumps([123, 456]),
        ]
        for corrupt in corrupted_inputs:
            res = validate_cookie_payload(corrupt, target_domain="autobotix.my.id")
            self.assertFalse(res.is_valid)
            self.assertEqual(res.status, SessionStatus.INVALID)
            self.assertTrue(len(res.reason) > 0)

    def test_profile_locking_prevents_concurrent_access(self):
        """Test that ProfileLock prevents two processes from using the same profile concurrently."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            profile_dir = Path(tmp_dir) / "test_user_profile"
            lock1 = ProfileLock(profile_dir)
            lock2 = ProfileLock(profile_dir)

            lock1.acquire()
            self.assertTrue(lock1.is_locked())

            # Second acquire on the same profile must raise ProfileLockedError
            with self.assertRaises(ProfileLockedError):
                lock2.acquire()

            # Once lock1 releases, lock2 can acquire successfully
            lock1.release()
            self.assertFalse(lock1.is_locked())

            lock2.acquire()
            self.assertTrue(lock2.is_locked())
            lock2.release()
            self.assertFalse(lock2.is_locked())

    def test_no_destructive_deletion_on_failure(self):
        """Test that failure to validate or verify does NOT delete or overwrite stored cookie."""
        past_time = time.time() - 7200
        expired_cookie_payload = json.dumps([
            {
                "name": "session",
                "value": "original_stored_token",
                "domain": "autobotix.my.id",
                "expirationDate": past_time,
            }
        ])
        db.save_cookie(self.test_email, expired_cookie_payload)

        sm = SessionManager()
        val_res = sm.validate_account_cookie(self.test_email, target_domain="autobotix.my.id")
        self.assertFalse(val_res.is_valid)
        self.assertEqual(val_res.status, SessionStatus.EXPIRED)

        # Stored cookie must STILL EXIST and remain completely unchanged
        stored = db.get_cookie_for_email(self.test_email)
        self.assertEqual(stored, expired_cookie_payload)

        # But status in database should be updated to 'expired'
        status_info = db.get_cookie_session_status(self.test_email)
        self.assertIsNotNone(status_info)
        self.assertEqual(status_info["status"], SessionStatus.EXPIRED.value)
        self.assertIn("kedaluwarsa", status_info["error_reason"].lower())

    def test_browser_restart_session_persistence(self):
        """Test that persistent profile retains session cookies across browser restart."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            profile_dir = Path(tmp_dir) / "persistent_profile"
            profile_dir.mkdir(parents=True, exist_ok=True)

            from seleniumbase import sb_cdp
            from mycdp import network as _cdp_net

            # 1. First run: Start browser on virtual display :99, inject cookie
            sb = sb_cdp.Chrome(
                "about:blank",
                headed=True,
                user_data_dir=str(profile_dir),
                chromium_arg="--disable-sync,--no-first-run,--no-default-browser-check",
            )
            try:
                sb.get("https://autobotix.my.id/")
                sb.sleep(1)

                future_ts = time.time() + 86400
                cdp_cookie = _cdp_net.CookieParam(
                    name="autobotix_persist_test",
                    value="token_persistent_abc",
                    domain=".autobotix.my.id",
                    path="/",
                    secure=True,
                    http_only=False,
                    expires=_cdp_net.TimeSinceEpoch(future_ts),
                )
                sb.set_all_cookies([cdp_cookie])
                sb.sleep(1)
            finally:
                session_manager.close_browser_session(sb)

            # 2. Restart browser: Re-open with SAME profile directory, do NOT inject cookie again
            sb2 = sb_cdp.Chrome(
                "about:blank",
                headed=True,
                user_data_dir=str(profile_dir),
                chromium_arg="--disable-sync,--no-first-run,--no-default-browser-check",
            )
            try:
                sb2.get("https://autobotix.my.id/")
                sb2.sleep(1)

                # Read all cookies from Chromium CDP
                loop = sb2.loop
                driver = sb2.driver
                loaded_cookies = loop.run_until_complete(driver.cookies.get_all())
                cookie_names = [c.name for c in loaded_cookies]
                self.assertIn("autobotix_persist_test", cookie_names)
            finally:
                session_manager.close_browser_session(sb2)


if __name__ == "__main__":
    unittest.main()
