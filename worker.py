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
            auto_replenish_drip_jobs()
            process_pending_jobs()
        except Exception as exc:
            log.exception("Unexpected error during job processing: %s", exc)

        log.info("Sleeping %ds before next check...", POLL_INTERVAL)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
