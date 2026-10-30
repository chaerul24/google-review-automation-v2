"""
Standalone review worker / scheduler.
Run independently from the Flask web app:

    python worker.py

Checks the database every 60 seconds for pending review jobs and processes
them sequentially, one business at a time.
"""

import argparse
import time
import logging
from datetime import datetime

from dotenv import load_dotenv

import db
import bot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

POLL_INTERVAL = 60  # seconds between checks


def process_pending_jobs():
    business_ids = db.get_businesses_with_pending()
    if not business_ids:
        log.info("No pending jobs found.")
        return

    for biz_id in business_ids:
        # Check if another process is actively running this business queue
        test_lock = bot.BusinessQueueLock(biz_id)
        if not test_lock.acquire():
            log.info("Business %s queue is already actively processed by another worker. Skipping.", biz_id)
            continue
        test_lock.release()

        biz = db.get_business(biz_id)
        if not biz:
            log.warning("Skipping business_id=%s — missing business.", biz_id)
            continue
        config = db.get_review_config(biz_id) or {
            "business_description": "",
            "review_style": "random",
            "delay_seconds": 60,
        }

        delay = max(5, int(config.get("delay_seconds") or 60))
        max_parallel = max(1, min(6, int(config.get("screen_count") or 6)))
        log.info(
            "Processing business '%s' (id=%s) with %ds delay and %d max screens.",
            biz["name"], biz_id, delay, max_parallel,
        )
        if max_parallel == 1:
            db.add_process_log(biz_id, f"Worker mulai memproses daftar antrean review secara berurutan (1 akun per waktu, jeda anti-bot {delay} detik).")
        else:
            db.add_process_log(biz_id, f"Worker mulai memproses antrean review (hingga {max_parallel} layar paralel).")
        bot.run_reviews(biz_id, biz, config, delay=delay, max_parallel=max_parallel)
        db.add_process_log(biz_id, "Worker selesai memproses antrean saat ini.")
        log.info("Finished business '%s' (id=%s).", biz["name"], biz_id)


def process_business(biz_id):
    """Process one business immediately, without the scheduler polling delay."""
    # Check if another process is actively running this business queue
    test_lock = bot.BusinessQueueLock(biz_id)
    if not test_lock.acquire():
        log.warning("Business %s queue is already actively running in another worker. Skipping.", biz_id)
        return
    test_lock.release()

    biz = db.get_business(biz_id)
    if not biz:
        db.add_process_log(biz_id, "Worker tidak dapat memulai: target bisnis tidak ditemukan.", level="error")
        return
    config = db.get_review_config(biz_id) or {
        "business_description": "",
        "review_style": "random",
        "delay_seconds": 60,
    }

    delay = max(5, int(config.get("delay_seconds") or 60))
    max_parallel = max(1, min(6, int(config.get("screen_count") or 6)))
    if max_parallel == 1:
        db.add_process_log(biz_id, f"Worker mulai langsung memproses daftar antrean review secara berurutan (1 akun per waktu, jeda anti-bot {delay} detik).")
    else:
        db.add_process_log(biz_id, f"Worker mulai langsung memproses review baru (hingga {max_parallel} layar paralel).")
    bot.run_reviews(biz_id, biz, config, delay=delay, max_parallel=max_parallel)
    db.add_process_log(biz_id, "Worker selesai memproses review saat ini.")


SESSION_KEEPALIVE_INTERVAL = 21600  # 6 hours
_last_keepalive_ts = 0.0


def periodic_session_keepalive(force: bool = False):
    """Keep Google account sessions alive.

    - OAuth accounts: validate via Google tokeninfo API; auto-refresh access token if needed.
    - Cookie accounts: ping myaccount.google.com to check session health.
    """
    global _last_keepalive_ts
    now = time.time()
    if not force and (now - _last_keepalive_ts < SESSION_KEEPALIVE_INTERVAL):
        return

    _last_keepalive_ts = now
    try:
        import requests as _req
        import session_manager
        with db.get_db() as conn:
            cookies = conn.execute(
                "SELECT id, email, cookie_json, auth_method, oauth_access_token, "
                "oauth_refresh_token, oauth_token_expiry, oauth_account_expiry "
                "FROM cookies ORDER BY id ASC"
            ).fetchall()

        if not cookies:
            return

        log.info("Starting background Google session keep-alive for %d accounts...", len(cookies))
        active_cnt = 0

        for row in cookies:
            cid = row["id"]
            email = row["email"]
            auth_method = row["auth_method"] or "cookie"

            try:
                # ── OAuth accounts ────────────────────────────────────────────
                if auth_method == "oauth":
                    # Check 30-day account grant expiry first
                    account_expiry = row["oauth_account_expiry"] or 0
                    if now > account_expiry:
                        with db.get_db() as conn:
                            conn.execute(
                                "UPDATE cookies SET status = 'expired', error_reason = ?, "
                                "last_checked_at = CURRENT_TIMESTAMP WHERE id = ?",
                                (db.OAUTH_ACCOUNT_EXPIRED_REASON, cid),
                            )
                        log.info("OAuth account %s 30-day grant expired.", email)
                        continue

                    # Validate / refresh the short-lived access token
                    token = db.get_valid_oauth_token(email)
                    if token:
                        # Quick tokeninfo ping
                        try:
                            ti = _req.get(
                                "https://www.googleapis.com/oauth2/v3/tokeninfo",
                                params={"access_token": token},
                                timeout=8,
                            )
                            if ti.status_code == 200:
                                st_val = "active"
                                reason = db.OAUTH_ACCOUNT_ACTIVE_REASON
                            else:
                                st_val = "needs_login"
                                reason = f"Tokeninfo HTTP {ti.status_code}"
                        except Exception as ping_err:
                            st_val = "active"  # network blip — assume OK
                            reason = db.OAUTH_ACCOUNT_ACTIVE_REASON
                            log.debug("OAuth tokeninfo ping failed for %s: %s", email, ping_err)
                    else:
                        st_val = "needs_login"
                        reason = "Gagal memperbarui token OAuth. Hubungkan ulang akun."

                    if st_val == "active":
                        active_cnt += 1
                    with db.get_db() as conn:
                        conn.execute(
                            "UPDATE cookies SET status = ?, error_reason = ?, "
                            "last_checked_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (st_val, reason, cid),
                        )
                        if st_val == "active":
                            conn.execute(
                                "UPDATE emails SET flagged = 0, fail_count = 0 WHERE email = ?",
                                (email,),
                            )

                # ── Cookie accounts ───────────────────────────────────────────
                else:
                    c_json = row["cookie_json"]
                    res = session_manager.check_google_account_live(c_json, fallback_email=email)
                    st_val = res.get("status") or "needs_login"
                    acc_name = res.get("account_name") or ""
                    reason = res.get("reason") or ""
                    if st_val == "active":
                        active_cnt += 1
                    with db.get_db() as conn:
                        conn.execute(
                            """UPDATE cookies
                               SET status = ?, account_name = (CASE WHEN ? != '' THEN ? ELSE account_name END),
                                   last_checked_at = CURRENT_TIMESTAMP, error_reason = ?
                               WHERE id = ?""",
                            (st_val, acc_name, acc_name, reason, cid),
                        )
                        if acc_name:
                            conn.execute("UPDATE emails SET account_name = ? WHERE email = ?", (acc_name, email))
                        if st_val == "active":
                            conn.execute("UPDATE emails SET flagged = 0, fail_count = 0 WHERE email = ?", (email,))

            except Exception as e:
                log.warning("Keepalive check failed for %s: %s", email, e)
            time.sleep(2)  # polite jitter between account pings

        log.info("Background Google session keep-alive complete: %d/%d accounts active.", active_cnt, len(cookies))
    except Exception as exc:
        log.warning("Error during periodic session keep-alive: %s", exc)


def auto_replenish_drip_jobs():
    """If drip campaign is enabled, ensure businesses with review goals have pending jobs queued."""
    try:
        settings = db.get_campaign_settings()
        if settings.get("is_paused"):
            return

        now = datetime.now()
        active_start = settings.get("active_hour_start", 8)
        active_end = settings.get("active_hour_end", 21)
        if not (active_start <= now.hour < active_end):
            log.info("Outside active campaign hours (%d:00 - %d:00). Drip queue sleeping.", active_start, active_end)
            return

        with db.get_db() as conn:
            businesses = conn.execute("SELECT id, name FROM businesses").fetchall()

        for biz in businesses:
            biz_id = biz["id"]
            with db.get_db() as conn:
                active_count = conn.execute(
                    "SELECT COUNT(*) FROM reviews WHERE business_id = ? AND status IN ('pending', 'reviewing')",
                    (biz_id,)
                ).fetchone()[0]

            if active_count == 0:
                config = db.get_review_config(biz_id)
                if not config:
                    continue
                created, _ = db.create_review_jobs(biz_id, [5], language_list=["Indonesian"])
                if created > 0:
                    log.info("Auto-Pilot: Queued %d new drip review job for business '%s' (id=%s).", created, biz["name"], biz_id)
                    db.add_process_log(biz_id, "Auto-Pilot: 1 tugas ulasan baru otomatis dijadwalkan.")
    except Exception as e:
        log.warning("Auto-replenish error: %s", e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-id", type=int, help="Process this business immediately, then exit.")
    args = parser.parse_args()

    db.init_db()
    db.migrate_add_delay_seconds()
    db.migrate_add_review_type_language()
    db.migrate_add_totp_secret()
    db.migrate_add_email_fail_tracking()
    db.migrate_add_cookies_table()
    db.migrate_add_cookie_session_columns()
    db.migrate_add_process_logs_table()
    if args.business_id:
        process_business(args.business_id)
        return

    db.reset_stuck_reviewing()
    log.info("Worker started. Reset any stuck 'reviewing' jobs to 'pending'.")
    log.info("Worker started. Polling every %ds for pending jobs.", POLL_INTERVAL)

    while True:
        try:
            periodic_session_keepalive()
            auto_replenish_drip_jobs()
            process_pending_jobs()
        except Exception as exc:
            log.exception("Unexpected error during job processing: %s", exc)

        log.info("Sleeping %ds before next check...", POLL_INTERVAL)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
