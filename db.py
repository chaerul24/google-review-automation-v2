import hashlib
import json
import random
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

DB_PATH = "reviews.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Global email pool (not tied to any business)
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                totp_secret TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Per-business review jobs: one row per (email, business) run
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER NOT NULL,
                business_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                review_text TEXT,
                star_rating INTEGER,
                review_type TEXT DEFAULT 'medium',
                review_language TEXT DEFAULT 'English',
                reviewed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails(id),
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            );

            CREATE TABLE IF NOT EXISTS review_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER UNIQUE NOT NULL,
                business_description TEXT DEFAULT '',
                review_style TEXT DEFAULT '',
                star_1_count INTEGER DEFAULT 0,
                star_2_count INTEGER DEFAULT 0,
                star_3_count INTEGER DEFAULT 0,
                star_4_count INTEGER DEFAULT 0,
                star_5_count INTEGER DEFAULT 0,
                delay_seconds INTEGER DEFAULT 60,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            );

            -- Google cookies per email (JSON dari browser)
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                cookie_json TEXT NOT NULL,
                status TEXT DEFAULT 'unknown',
                last_checked_at TIMESTAMP,
                error_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS process_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                review_id INTEGER,
                level TEXT NOT NULL DEFAULT 'info',
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id),
                FOREIGN KEY (review_id) REFERENCES reviews(id)
            );
        """)
    migrate_add_cookie_session_columns()
    migrate_add_account_name()
    migrate_add_screen_count()
    migrate_add_gemini_config()
    init_templates_and_campaigns_db()
    ensure_all_businesses_have_config()
    sync_active_cookies_to_emails()


def migrate_add_account_name():
    """Ensure account_name column exists in cookies and emails tables."""
    with get_db() as conn:
        cols_c = [r["name"] for r in conn.execute("PRAGMA table_info(cookies)").fetchall()]
        if "account_name" not in cols_c:
            conn.execute("ALTER TABLE cookies ADD COLUMN account_name TEXT DEFAULT ''")

        cols_e = [r["name"] for r in conn.execute("PRAGMA table_info(emails)").fetchall()]
        if "account_name" not in cols_e:
            conn.execute("ALTER TABLE emails ADD COLUMN account_name TEXT DEFAULT ''")


def sync_active_cookies_to_emails():
    with get_db() as conn:
        conn.execute("""
            UPDATE emails
            SET flagged = 0, fail_count = 0
            WHERE email IN (SELECT email FROM cookies WHERE status = 'active')
        """)


def ensure_all_businesses_have_config():
    with get_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO review_configs
            (business_id, business_description, review_style, star_1_count, star_2_count, star_3_count, star_4_count, star_5_count, delay_seconds)
            SELECT id, '', 'random', 0, 0, 0, 0, 0, 60
            FROM businesses
            WHERE id NOT IN (SELECT business_id FROM review_configs)
        """)


def migrate_autobotix():
    """Non-destructive inventory tables for the AutoBotix read-only module."""
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS ab_tunnels (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, uuid TEXT, status TEXT, status_source TEXT, config_file TEXT, observed_at TEXT, evidence TEXT);
        CREATE TABLE IF NOT EXISTS ab_domains (id INTEGER PRIMARY KEY, hostname TEXT NOT NULL UNIQUE, tunnel_name TEXT, tunnel_uuid TEXT, config_file TEXT, ingress_rule TEXT, target_url TEXT, target_host TEXT, target_port INTEGER, proxy_type TEXT, service_name TEXT, container_name TEXT, project_path TEXT, framework TEXT, upstream_status TEXT, public_https_status TEXT, public_https_reason TEXT, project_mapping_status TEXT, evidence TEXT, confidence TEXT, observed_at TEXT, source TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ab_health_checks (id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, layer TEXT NOT NULL, status TEXT NOT NULL, http_status INTEGER, reason TEXT, duration_ms REAL, checked_at TEXT NOT NULL, source TEXT NOT NULL, FOREIGN KEY(domain_id) REFERENCES ab_domains(id));
        CREATE TABLE IF NOT EXISTS ab_findings (id INTEGER PRIMARY KEY, domain_id INTEGER, severity TEXT NOT NULL, finding TEXT NOT NULL, evidence TEXT, recommendation TEXT, observed_at TEXT, source TEXT NOT NULL, FOREIGN KEY(domain_id) REFERENCES ab_domains(id));
        CREATE TABLE IF NOT EXISTS ab_resource_metrics (id INTEGER PRIMARY KEY, metric TEXT NOT NULL, value REAL, unit TEXT NOT NULL, scope TEXT NOT NULL, observed_at TEXT NOT NULL, validity TEXT NOT NULL, source TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ab_services (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, port INTEGER, project_path TEXT, status TEXT, observed_at TEXT, source TEXT NOT NULL, evidence TEXT);
        CREATE TABLE IF NOT EXISTS ab_activity_logs (id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT, outcome TEXT NOT NULL, message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_ab_health_domain_time ON ab_health_checks(domain_id, checked_at DESC);
        """)


def log_autobotix_activity(actor, action, target, outcome, message=None):
    with get_db() as conn:
        conn.execute("INSERT INTO ab_activity_logs(actor,action,target,outcome,message) VALUES(?,?,?,?,?)", (actor, action, target, outcome, message))


def get_autobotix_domains(search="", status=""):
    query = "SELECT * FROM ab_domains WHERE 1=1"
    params = []
    if search:
        query += " AND hostname LIKE ?"; params.append(f"%{search}%")
    if status:
        query += " AND upstream_status = ?"; params.append(status)
    query += " ORDER BY hostname"
    with get_db() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_autobotix_domain(domain_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM ab_domains WHERE id=?", (domain_id,)).fetchone()
        if not row: return None
        result = dict(row)
        result["history"] = [dict(r) for r in conn.execute("SELECT * FROM ab_health_checks WHERE domain_id=? ORDER BY checked_at DESC LIMIT 30", (domain_id,)).fetchall()]
        result["findings"] = [dict(r) for r in conn.execute("SELECT * FROM ab_findings WHERE domain_id=? ORDER BY id DESC", (domain_id,)).fetchall()]
        return result


def get_autobotix_tunnels():
    with get_db() as conn:
        return [dict(r) for r in conn.execute("SELECT t.*, COUNT(d.id) AS domain_count FROM ab_tunnels t LEFT JOIN ab_domains d ON d.tunnel_name=t.name GROUP BY t.id ORDER BY t.name").fetchall()]


def get_autobotix_tunnel(tunnel_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM ab_tunnels WHERE id=?", (tunnel_id,)).fetchone()
        if not row: return None
        result = dict(row); result["domains"] = [dict(r) for r in conn.execute("SELECT * FROM ab_domains WHERE tunnel_name=? ORDER BY hostname", (result["name"],)).fetchall()]
        return result


def get_autobotix_summary():
    """Inventory counts remain historical; callers must display their source/time."""
    with get_db() as conn:
        return dict(conn.execute("""
            SELECT
              (SELECT COUNT(*) FROM ab_tunnels) AS tunnel_count,
              (SELECT COUNT(*) FROM ab_domains) AS domain_count,
              (SELECT COUNT(*) FROM ab_services) AS service_count,
              (SELECT COUNT(*) FROM ab_domains WHERE upstream_status = 'healthy') AS historical_healthy_domains,
              (SELECT MAX(observed_at) FROM ab_domains) AS inventory_observed_at
        """).fetchone())


def get_autobotix_services():
    with get_db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM ab_services ORDER BY name").fetchall()]


# ── Businesses ────────────────────────────────────────────────────────────────

def get_all_businesses():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT b.*,
                   COUNT(CASE WHEN r.status = 'reviewed' THEN 1 END) AS reviewed_count,
                   COUNT(r.id) AS assigned_emails
            FROM businesses b
            LEFT JOIN reviews r ON r.business_id = b.id
            GROUP BY b.id
            ORDER BY b.created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_business(business_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM businesses WHERE id = ?", (business_id,)
        ).fetchone()
        return dict(row) if row else None


def add_business(name, url):
    with get_db() as conn:
        cur = conn.execute("INSERT INTO businesses (name, url) VALUES (?, ?)", (name, url))
        biz_id = cur.lastrowid
        conn.execute(
            """INSERT OR IGNORE INTO review_configs
               (business_id, business_description, review_style, star_1_count, star_2_count, star_3_count, star_4_count, star_5_count, delay_seconds)
               VALUES (?, '', 'random', 0, 0, 0, 0, 0, 60)""",
            (biz_id,),
        )
        return biz_id


def delete_business(business_id):
    with get_db() as conn:
        conn.execute("DELETE FROM process_logs WHERE business_id = ?", (business_id,))
        conn.execute("DELETE FROM reviews WHERE business_id = ?", (business_id,))
        conn.execute("DELETE FROM review_configs WHERE business_id = ?", (business_id,))
        conn.execute("DELETE FROM businesses WHERE id = ?", (business_id,))


# ── Global Email Pool ─────────────────────────────────────────────────────────

def get_all_emails():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT e.*,
                      c.cookie_json,
                      c.status AS cookie_status,
                      c.updated_at AS cookie_updated_at,
                      c.error_reason AS cookie_error_reason
               FROM emails e
               LEFT JOIN cookies c ON e.email = c.email
               ORDER BY 
                   (CASE WHEN c.status = 'active' THEN 0 ELSE 1 END) ASC,
                   COALESCE(e.flagged, 0) ASC,
                   e.id DESC"""
        ).fetchall()

        parsed = []
        sig_counts = defaultdict(int)
        for r in rows:
            d = dict(r)
            sig = None
            if d.get("cookie_json"):
                try:
                    cdata = json.loads(d["cookie_json"])
                    for ck in cdata:
                        if ck.get("name") in ("SID", "SAPISID", "__Secure-1PSID"):
                            val_str = str(ck.get("value") or "")
                            if val_str:
                                sig = hashlib.sha256(val_str.encode("utf-8")).hexdigest()[:8]
                                break
                except Exception:
                    pass
            d.pop("cookie_json", None)  # Don't expose raw cookie JSON
            d["session_hash"] = sig
            if sig:
                sig_counts[sig] += 1
            parsed.append(d)

        for d in parsed:
            d["is_duplicate"] = bool(d.get("session_hash") and sig_counts[d["session_hash"]] > 1)

        return parsed


def count_emails():
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM emails").fetchone()
        return row["cnt"]


def count_queued_for_business(business_id):
    """Number of emails already pending or reviewing for this business."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reviews WHERE business_id = ? AND status IN ('pending','reviewing')",
            (business_id,),
        ).fetchone()
        return row["cnt"]


def count_reviewed_for_business(business_id):
    """Number of emails that have already successfully reviewed this business."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reviews WHERE business_id = ? AND status = 'reviewed'",
            (business_id,),
        ).fetchone()
        return row["cnt"]


def get_analytics_summary():
    """Aggregated stats and trend metrics for professional SaaS dashboard."""
    with get_db() as conn:
        # Star distribution
        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        rows = conn.execute(
            "SELECT star_rating, COUNT(*) as count FROM reviews WHERE status = 'reviewed' AND star_rating IS NOT NULL GROUP BY star_rating"
        ).fetchall()
        for r in rows:
            rating = r["star_rating"]
            if rating in star_counts:
                star_counts[rating] = r["count"]

        # 7-day trend
        trend_rows = conn.execute(
            "SELECT DATE(COALESCE(reviewed_at, created_at)) as day, COUNT(*) as count "
            "FROM reviews WHERE status = 'reviewed' "
            "GROUP BY day ORDER BY day DESC LIMIT 7"
        ).fetchall()
        daily_trends = [{"day": r["day"], "count": r["count"]} for r in reversed(trend_rows)]
        if not daily_trends:
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_trends = [{"day": today_str, "count": 0}]

        total_reviewed = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'reviewed'").fetchone()[0]
        total_pending = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'pending'").fetchone()[0]
        total_failed = conn.execute("SELECT COUNT(*) FROM reviews WHERE status IN ('failed', 'flagged')").fetchone()[0]
        total_attempts = total_reviewed + total_failed
        success_rate = round((total_reviewed / total_attempts * 100), 1) if total_attempts > 0 else 100.0

        total_cookies = conn.execute("SELECT COUNT(*) FROM cookies").fetchone()[0]
        valid_cookies = conn.execute("SELECT COUNT(*) FROM cookies WHERE status = 'active' OR status IS NULL").fetchone()[0]
        cookie_health = round((valid_cookies / total_cookies * 100), 1) if total_cookies > 0 else 100.0

        return {
            "star_distribution": star_counts,
            "daily_trends": daily_trends,
            "total_reviewed": total_reviewed,
            "total_pending": total_pending,
            "total_failed": total_failed,
            "success_rate": success_rate,
            "cookie_health": cookie_health,
        }


def add_email(email, password, totp_secret=None):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM emails WHERE email = ?", (email,)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO emails (email, password, totp_secret) VALUES (?, ?, ?)",
                (email, password, totp_secret),
            )
            return True
        else:
            conn.execute(
                "UPDATE emails SET password = ?, totp_secret = ? WHERE email = ?",
                (password, totp_secret, email),
            )
            return False


def delete_email(email_id):
    with get_db() as conn:
        conn.execute("DELETE FROM reviews WHERE email_id = ?", (email_id,))
        conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))


# ── Per-business Reviews ──────────────────────────────────────────────────────

def get_reviews_for_business(business_id):
    """Returns all review jobs for a business joined with email credentials."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT r.*, e.email, e.password, e.totp_secret
               FROM reviews r
               JOIN emails e ON e.id = r.email_id
               WHERE r.business_id = ?
               ORDER BY r.created_at ASC""",
            (business_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_review_for_business(review_id, business_id):
    """Return one review job with account details, scoped to a business."""
    with get_db() as conn:
        row = conn.execute(
            """SELECT r.*, e.email, e.password, e.totp_secret
               FROM reviews r JOIN emails e ON e.id = r.email_id
               WHERE r.id = ? AND r.business_id = ?""",
            (review_id, business_id),
        ).fetchone()
        return dict(row) if row else None


def get_pending_reviews(business_id):
    """Emails assigned to this business run that haven't been posted yet.
    Excludes emails that have been flagged after too many failures.
    Strictly limited to accounts with active cookies ('active').
    """
    with get_db() as conn:
        rows = conn.execute(
            """SELECT r.*, e.email, e.password, e.totp_secret, COALESCE(c.account_name, e.account_name, '') AS account_name, c.status AS cookie_status
               FROM reviews r
               JOIN emails e ON e.id = r.email_id
               JOIN cookies c ON e.email = c.email
               WHERE r.business_id = ? AND r.status = 'pending'
                 AND COALESCE(e.flagged, 0) = 0
                 AND c.status = 'active'
               ORDER BY r.created_at ASC""",
            (business_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def create_review_jobs(business_id, star_list, type_list=None, language_list=None, allowed_email_ids=None):
    """
    Assign emails from the global pool to this business run.
    star_list is an ordered list like [5, 5, 4, 4, 1] — one entry per email.
    type_list is an ordered list like ['short', 'long', 'no_text', 'medium'].
    language_list is an ordered list like ['English', 'Spanish', 'French'].
    allowed_email_ids: optional list of email IDs to restrict assignment to.
                       If None, all emails in the pool are eligible.
    All three lists are pre-shuffled by the caller for randomness.
    Already-pending emails are skipped and counted separately.
    Returns (newly_created, already_pending).
    """
    n = len(star_list)
    # Pad type_list with 'medium' if shorter than star_list
    effective_types = list(type_list or [])
    while len(effective_types) < n:
        effective_types.append('medium')
    effective_types = effective_types[:n]

    # Pad language_list with 'Indonesian' if shorter than star_list
    effective_langs = list(language_list or [])
    while len(effective_langs) < n:
        effective_langs.append('Indonesian')
    effective_langs = effective_langs[:n]

    with get_db() as conn:
        # Sync: Any email that has an active cookie in cookies table is unflagged
        conn.execute("""
            UPDATE emails
            SET flagged = 0, fail_count = 0
            WHERE email IN (SELECT email FROM cookies WHERE status = 'active')
        """)

        # Emails already assigned to this business with pending status
        pending_email_ids = {
            r["email_id"]
            for r in conn.execute(
                "SELECT email_id FROM reviews WHERE business_id = ? AND status = 'pending'",
                (business_id,),
            ).fetchall()
        }

        # Emails that have completed a review or are currently reviewing or pending
        active_or_done = {
            r["email_id"]
            for r in conn.execute(
                "SELECT email_id FROM reviews WHERE business_id = ? AND status IN ('reviewed', 'reviewing', 'pending')",
                (business_id,),
            ).fetchall()
        }

        # Any previous failed or flagged review rows for this business that can be retried
        recoverable_reviews = {
            r["email_id"]: r["id"]
            for r in conn.execute(
                "SELECT email_id, id FROM reviews WHERE business_id = ? AND status IN ('failed', 'flagged')",
                (business_id,),
            ).fetchall()
        }

        # Pull unflagged emails from pool that are not in active_or_done
        # Prioritize active cookies, deduplicate sessions, and shuffle randomly
        all_emails = conn.execute(
            """SELECT e.id, e.email, c.cookie_json, c.status AS cookie_status
               FROM emails e
               LEFT JOIN cookies c ON e.email = c.email
               WHERE COALESCE(e.flagged, 0) = 0"""
        ).fetchall()

        seen_emails = set()
        seen_sessions = set()
        active_cookie_ids = []
        other_ids = []

        for r_row in all_emails:
            r = dict(r_row)
            if r["id"] in active_or_done:
                continue
            if allowed_email_ids is not None and r["id"] not in set(allowed_email_ids):
                continue
            if r["email"] in seen_emails:
                continue
            seen_emails.add(r["email"])

            # Deduplicate session tokens so the same Google account is never assigned across multiple slots
            sess_sig = None
            if r.get("cookie_json"):
                try:
                    citems = json.loads(r["cookie_json"])
                    if isinstance(citems, list):
                        for ck in citems:
                            if ck.get("name") in ("SID", "SAPISID", "__Secure-1PSID") and ck.get("value"):
                                sess_sig = hashlib.sha256(str(ck["value"]).encode()).hexdigest()[:12]
                                break
                except Exception:
                    pass

            if sess_sig:
                if sess_sig in seen_sessions:
                    # Skip duplicate session token from the same Google account
                    continue
                seen_sessions.add(sess_sig)

            if r["cookie_status"] == "active":
                active_cookie_ids.append(r["id"])
            # Hanya akun dengan cookie aktif ('active') yang diikutsertakan ke dalam antrean task

        # Acak urutan akun aktif
        random.shuffle(active_cookie_ids)
        available = active_cookie_ids
        if not available:
            return 0, len(pending_email_ids)

        count = 0
        for idx, (star, rtype, lang) in enumerate(zip(star_list, effective_types, effective_langs)):
            if idx >= len(available):
                break
            email_id = available[idx]
            if email_id in recoverable_reviews:
                # Reuse and reactivate existing failed or flagged review row
                conn.execute(
                    """UPDATE reviews
                       SET status = 'pending', star_rating = ?, review_type = ?, review_language = ?,
                           review_text = NULL, reviewed_at = NULL, created_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (star, rtype, lang, recoverable_reviews[email_id]),
                )
            else:
                conn.execute(
                    "INSERT INTO reviews (email_id, business_id, star_rating, review_type, review_language, status) "
                    "VALUES (?, ?, ?, ?, ?, 'pending')",
                    (email_id, business_id, star, rtype, lang),
                )
            count += 1
        return count, len(pending_email_ids)


def get_businesses_with_pending():
    """Return list of business_ids that have at least one pending review job."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT business_id FROM reviews WHERE status = 'pending'"
        ).fetchall()
        return [r["business_id"] for r in rows]


def migrate_add_delay_seconds():
    """Add delay_seconds column if it doesn't exist (safe to call multiple times)."""
    with get_db() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(review_configs)").fetchall()]
        if "delay_seconds" not in cols:
            conn.execute(
                "ALTER TABLE review_configs ADD COLUMN delay_seconds INTEGER DEFAULT 60"
            )


def migrate_add_screen_count():
    """Add screen_count column if it doesn't exist (safe to call multiple times)."""
    with get_db() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(review_configs)").fetchall()]
        if "screen_count" not in cols:
            conn.execute(
                "ALTER TABLE review_configs ADD COLUMN screen_count INTEGER DEFAULT 3"
            )


def migrate_add_gemini_config():
    """Add gemini_token and business_category columns if they don't exist."""
    with get_db() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(review_configs)").fetchall()]
        if "gemini_token" not in cols:
            conn.execute(
                "ALTER TABLE review_configs ADD COLUMN gemini_token TEXT DEFAULT ''"
            )
        if "business_category" not in cols:
            conn.execute(
                "ALTER TABLE review_configs ADD COLUMN business_category TEXT DEFAULT ''"
            )


def migrate_add_review_type_language():
    """Add review_type and review_language columns to reviews table (safe to call multiple times)."""
    with get_db() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(reviews)").fetchall()]
        if "review_type" not in cols:
            conn.execute("ALTER TABLE reviews ADD COLUMN review_type TEXT DEFAULT 'medium'")
        if "review_language" not in cols:
            conn.execute("ALTER TABLE reviews ADD COLUMN review_language TEXT DEFAULT 'English'")


def migrate_add_totp_secret():
    """Add totp_secret column to emails table (safe to call multiple times)."""
    with get_db() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(emails)").fetchall()]
        if "totp_secret" not in cols:
            conn.execute("ALTER TABLE emails ADD COLUMN totp_secret TEXT")


def migrate_add_email_fail_tracking():
    """Add fail_count and flagged columns to emails table (safe to call multiple times)."""
    with get_db() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(emails)").fetchall()]
        if "fail_count" not in cols:
            conn.execute("ALTER TABLE emails ADD COLUMN fail_count INTEGER DEFAULT 0")
        if "flagged" not in cols:
            conn.execute("ALTER TABLE emails ADD COLUMN flagged INTEGER DEFAULT 0")


def increment_email_fail_count(email_id, threshold=5):
    """Increment the fail counter for an email.
    If it reaches *threshold*, mark the email as flagged and set all its
    pending/reviewing review jobs to 'flagged' so they are never retried.
    Returns True if the email was just flagged, False otherwise.
    """
    with get_db() as conn:
        conn.execute(
            "UPDATE emails SET fail_count = fail_count + 1 WHERE id = ?",
            (email_id,),
        )
        row = conn.execute(
            "SELECT fail_count, flagged FROM emails WHERE id = ?", (email_id,)
        ).fetchone()
        if row and row["fail_count"] >= threshold and not row["flagged"]:
            conn.execute(
                "UPDATE emails SET flagged = 1 WHERE id = ?", (email_id,)
            )
            conn.execute(
                "UPDATE reviews SET status = 'flagged' "
                "WHERE email_id = ? AND status IN ('pending', 'reviewing')",
                (email_id,),
            )
            return True
        return False


def unflag_email(email_id):
    """Explicitly re-enable one email account after its session is repaired.

    This does not alter review history or requeue flagged jobs.
    """
    with get_db() as conn:
        result = conn.execute(
            "UPDATE emails SET flagged = 0, fail_count = 0 WHERE id = ?",
            (email_id,),
        )
        return result.rowcount > 0


def unflag_all_emails():
    """Reset flagged and fail_count for all accounts in the pool."""
    with get_db() as conn:
        result = conn.execute(
            "UPDATE emails SET flagged = 0, fail_count = 0"
        )
        return result.rowcount


def reset_stuck_reviewing():
    """Reset any jobs stuck in 'reviewing' state back to 'pending'.
    Called on worker startup to recover from a crash or kill signal."""
    with get_db() as conn:
        conn.execute(
            "UPDATE reviews SET status = 'pending' WHERE status = 'reviewing'"
        )


def reset_business_reviewing(business_id):
    """Return only a business's interrupted jobs to the pending state."""
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE reviews SET status = 'pending' "
            "WHERE business_id = ? AND status = 'reviewing'",
            (business_id,),
        )
        return cur.rowcount


def delete_business_queue(business_id):
    """Delete only pending/in-progress queue rows; preserve review history."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id FROM reviews WHERE business_id = ? AND status IN ('pending', 'reviewing')",
            (business_id,),
        ).fetchall()
        ids = [row["id"] for row in rows]
        if ids:
            placeholders = ",".join("?" for _ in ids)
            conn.execute(f"DELETE FROM process_logs WHERE review_id IN ({placeholders})", ids)
            conn.execute(
                f"DELETE FROM reviews WHERE id IN ({placeholders})", ids
            )
        return len(ids)


def reset_review(review_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE reviews SET status = 'pending', review_text = NULL, "
            "star_rating = NULL, reviewed_at = NULL WHERE id = ?",
            (review_id,),
        )


def reset_all_reviews_for_business(business_id):
    """Reset all reviews for a business to pending state so they can be re-run."""
    with get_db() as conn:
        cur = conn.execute(
            """UPDATE reviews
               SET status = 'pending', review_text = NULL, star_rating = COALESCE(star_rating, 5), reviewed_at = NULL
               WHERE business_id = ?""",
            (business_id,),
        )
        conn.execute("DELETE FROM process_logs WHERE business_id = ?", (business_id,))
        return cur.rowcount


def delete_all_reviews_for_business(business_id):
    """Delete all reviews and associated process logs for a business (Dark Mode - Hapus Komentar)."""
    with get_db() as conn:
        conn.execute("DELETE FROM process_logs WHERE business_id = ?", (business_id,))
        cur = conn.execute("DELETE FROM reviews WHERE business_id = ?", (business_id,))
        return cur.rowcount


def delete_review(review_id):
    with get_db() as conn:
        conn.execute("DELETE FROM process_logs WHERE review_id = ?", (review_id,))
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))


# ── Per-business process log ─────────────────────────────────────────────────

def add_process_log(business_id, message, review_id=None, level="info"):
    """Store a human-readable progress event for the dashboard."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO process_logs (business_id, review_id, level, message) VALUES (?, ?, ?, ?)",
            (business_id, review_id, level, str(message)[:1000]),
        )


def clear_process_logs(business_id):
    """Start a clean live-log session for the next run."""
    with get_db() as conn:
        conn.execute("DELETE FROM process_logs WHERE business_id = ?", (business_id,))


def get_process_logs(business_id, limit=80):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT pl.id, pl.review_id, pl.level, pl.message, pl.created_at,
                      COALESCE(e.email, e2.email, '') AS email,
                      COALESCE(e.account_name, e2.account_name, c.account_name, '') AS account_name
               FROM process_logs pl
               LEFT JOIN emails e ON pl.review_id = e.id
               LEFT JOIN reviews r ON pl.review_id = r.id
               LEFT JOIN emails e2 ON r.email_id = e2.id
               LEFT JOIN cookies c ON COALESCE(e.email, e2.email) = c.email
               WHERE pl.business_id = ?
               ORDER BY pl.id DESC LIMIT ?""",
            (business_id, limit),
        ).fetchall()
        logs = []
        for row in reversed(rows):
            item = dict(row)
            # SQLite CURRENT_TIMESTAMP is UTC; dashboard users are in WIB.
            try:
                created = datetime.strptime(item["created_at"], "%Y-%m-%d %H:%M:%S")
                item["created_at"] = (created + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                pass
            logs.append(item)
        return logs


def migrate_add_process_logs_table():
    """Create the process log table for existing databases."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS process_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                review_id INTEGER,
                level TEXT NOT NULL DEFAULT 'info',
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id),
                FOREIGN KEY (review_id) REFERENCES reviews(id)
            )
        """)


def update_review_status(review_id, status, review_text=None, star_rating=None):
    with get_db() as conn:
        if status == "reviewed":
            conn.execute(
                "UPDATE reviews SET status = ?, review_text = ?, star_rating = ?, "
                "reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, review_text, star_rating, review_id),
            )
        else:
            conn.execute(
                "UPDATE reviews SET status = ?, review_text = ?, star_rating = ? WHERE id = ?",
                (status, review_text, star_rating, review_id),
            )


# ── Review Config ─────────────────────────────────────────────────────────────

def get_review_config(business_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM review_configs WHERE business_id = ?", (business_id,)
        ).fetchone()
        if row:
            return dict(row)
        biz = conn.execute("SELECT id FROM businesses WHERE id = ?", (business_id,)).fetchone()
        if biz:
            conn.execute(
                """INSERT OR IGNORE INTO review_configs
                   (business_id, business_description, review_style, star_1_count, star_2_count, star_3_count, star_4_count, star_5_count, delay_seconds)
                   VALUES (?, '', 'random', 0, 0, 0, 0, 0, 60)""",
                (business_id,),
            )
            created = conn.execute(
                "SELECT * FROM review_configs WHERE business_id = ?", (business_id,)
            ).fetchone()
            if created:
                return dict(created)
        return None


def save_review_config(business_id, config):
    screen_count = max(1, min(6, int(config.get("screen_count") or 6)))
    gemini_token = (config.get("gemini_token") or "").strip()
    business_category = (config.get("business_category") or "").strip()
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM review_configs WHERE business_id = ?", (business_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE review_configs SET
                       business_description = ?,
                       review_style = ?,
                       star_1_count = ?,
                       star_2_count = ?,
                       star_3_count = ?,
                       star_4_count = ?,
                       star_5_count = ?,
                       delay_seconds = ?,
                       screen_count = ?,
                       gemini_token = ?,
                       business_category = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE business_id = ?""",
                (
                    config["business_description"],
                    config["review_style"],
                    config["star_1_count"],
                    config["star_2_count"],
                    config["star_3_count"],
                    config["star_4_count"],
                    config["star_5_count"],
                    config.get("delay_seconds", 60),
                    screen_count,
                    gemini_token,
                    business_category,
                    business_id,
                ),
            )
        else:
            conn.execute(
                """INSERT INTO review_configs
                       (business_id, business_description, review_style,
                        star_1_count, star_2_count, star_3_count, star_4_count, star_5_count,
                        delay_seconds, screen_count, gemini_token, business_category)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    business_id,
                    config["business_description"],
                    config["review_style"],
                    config["star_1_count"],
                    config["star_2_count"],
                    config["star_3_count"],
                    config["star_4_count"],
                    config["star_5_count"],
                    config.get("delay_seconds", 60),
                    screen_count,
                    gemini_token,
                    business_category,
                ),
            )


# ── Google Cookies ────────────────────────────────────────────────────────────

def enrich_cookies_with_duplicate_info(cookies_list):
    """Detect if multiple accounts share the same Google session tokens (SID / SAPISID)."""
    import hashlib
    sig_map = {}
    for c in cookies_list:
        raw = c.get("cookie_json") or ""
        sig = None
        try:
            items = json.loads(raw)
            if isinstance(items, list):
                for ck in items:
                    if isinstance(ck, dict) and ck.get("name") in ("SID", "SAPISID", "__Secure-1PSID"):
                        val = str(ck.get("value") or "").strip()
                        if val:
                            sig = hashlib.sha256(val.encode("utf-8")).hexdigest()[:12]
                            break
        except Exception:
            pass
        c["_session_sig"] = sig
        if sig:
            sig_map.setdefault(sig, []).append(c.get("email"))

    for c in cookies_list:
        sig = c.get("_session_sig")
        if sig and len(sig_map.get(sig, [])) > 1:
            c["is_duplicate"] = True
            c["duplicate_with"] = [em for em in sig_map[sig] if em != c.get("email")]
        else:
            c["is_duplicate"] = False
            c["duplicate_with"] = []
        c.pop("_session_sig", None)
    return cookies_list


def get_all_cookies():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM cookies ORDER BY updated_at DESC"
        ).fetchall()
        cookies_list = [dict(r) for r in rows]
        return enrich_cookies_with_duplicate_info(cookies_list)


def get_cookie_for_email(email):
    """Return cookie_json string for an email, or None if not found."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT cookie_json FROM cookies WHERE email = ?", (email,)
        ).fetchone()
        return row["cookie_json"] if row else None


def save_cookie(email, cookie_json):
    """Insert or update cookie for an email."""
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM cookies WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE cookies SET cookie_json = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
                (cookie_json, email),
            )
            return False  # updated
        else:
            conn.execute(
                "INSERT INTO cookies (email, cookie_json) VALUES (?, ?)",
                (email, cookie_json),
            )
            return True  # inserted


def delete_cookie(cookie_id):
    with get_db() as conn:
        row = conn.execute("SELECT email FROM cookies WHERE id = ?", (cookie_id,)).fetchone()
        if row:
            email = row["email"]
            conn.execute("DELETE FROM cookies WHERE id = ?", (cookie_id,))
            if email.startswith("google.session."):
                conn.execute("DELETE FROM emails WHERE email = ?", (email,))


def migrate_add_cookies_table():
    """Create cookies table if it doesn't exist (safe to call multiple times)."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                cookie_json TEXT NOT NULL,
                status TEXT DEFAULT 'unknown',
                last_checked_at TIMESTAMP,
                error_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    migrate_add_cookie_session_columns()


def migrate_add_cookie_session_columns():
    """Add status, last_checked_at, and error_reason columns to cookies table."""
    with get_db() as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(cookies)").fetchall()]
        if "status" not in cols:
            conn.execute("ALTER TABLE cookies ADD COLUMN status TEXT DEFAULT 'unknown'")
        if "last_checked_at" not in cols:
            conn.execute("ALTER TABLE cookies ADD COLUMN last_checked_at TIMESTAMP")
        if "error_reason" not in cols:
            conn.execute("ALTER TABLE cookies ADD COLUMN error_reason TEXT")


def update_cookie_session_status(email, status, error_reason=None):
    """Non-destructively update cookie session status and error reason without overwriting cookies."""
    with get_db() as conn:
        conn.execute(
            """UPDATE cookies 
               SET status = ?, last_checked_at = CURRENT_TIMESTAMP, error_reason = ? 
               WHERE email = ?""",
            (status, error_reason, email),
        )


def get_cookie_session_status(email):
    """Retrieve session status metadata for an email."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, email, status, last_checked_at, error_reason, updated_at FROM cookies WHERE email = ?",
            (email,),
        ).fetchone()
        return dict(row) if row else None


# ── Review Templates & AI Studio ──────────────────────────────────────────────

def init_templates_and_campaigns_db():
    """Initializes tables for review studio templates and drip campaign scheduler."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS review_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Umum',
                persona TEXT NOT NULL DEFAULT 'local_guide',
                star_rating INTEGER NOT NULL DEFAULT 5,
                prompt_template TEXT NOT NULL,
                keywords TEXT DEFAULT '',
                sample_output TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS campaign_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                drip_min_delay INTEGER DEFAULT 30,
                drip_max_delay INTEGER DEFAULT 90,
                active_hour_start INTEGER DEFAULT 8,
                active_hour_end INTEGER DEFAULT 21,
                anti_spam_jitter INTEGER DEFAULT 25,
                is_paused INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Ensure default campaign settings exist
        row = conn.execute("SELECT id FROM campaign_settings WHERE id = 1").fetchone()
        if not row:
            conn.execute("""
                INSERT INTO campaign_settings (id, drip_min_delay, drip_max_delay, active_hour_start, active_hour_end, anti_spam_jitter, is_paused)
                VALUES (1, 30, 90, 8, 21, 25, 0)
            """)

        # Seed initial preset templates if empty
        count = conn.execute("SELECT COUNT(*) FROM review_templates").fetchone()[0]
        if count == 0:
            defaults = [
                (
                    "Kafe & Coffee Shop Kekinian",
                    "Kafe & Kuliner",
                    "foodie",
                    5,
                    "Ulasan kafe modern dengan fokus pada kenikmatan rasa racikan kopi, kenyamanan tempat nugas, keramahan barista, dan fasilitas wi-fi kencang.",
                    "kopi enak, suasana nyaman, barista ramah, wi-fi kencang, spot foto estetik",
                    "Salah satu coffee shop terfavorit di kawasan ini! Kopinya nikmat dengan balance rasa yang pas. Tempatnya adem dan nyaman sekali untuk nugas atau santai bersama teman.",
                ),
                (
                    "Klinik Dokter & Layanan Medis",
                    "Kesehatan",
                    "local_guide",
                    5,
                    "Ulasan klinik kesehatan yang menonjolkan higienitas ruangan, ketenangan suasana, penjelasan dokter yang informatif dan ramah, serta penanganan cepat.",
                    "dokter ramah, penjelasan detail, tempat bersih, antrean teratur, staf responsif",
                    "Pelayanan medis yang sangat profesional dan memuaskan. Dokter memeriksa dengan teliti dan komunikatif, menjelaskan kondisi dengan bahasa yang mudah dipahami.",
                ),
                (
                    "Hotel & Penginapan Staycation",
                    "Hospitality",
                    "family",
                    5,
                    "Ulasan hotel ramah keluarga dengan ulasan kebersihan kamar, keramahan resepsionis, menu sarapan bervariasi, dan lokasi yang strategis.",
                    "kamar bersih, kasur empuk, sarapan lezat, lokasi strategis, kolam renang anak",
                    "Pengalaman menginap yang luar biasa menyenangkan bersama keluarga. Kamar sangat bersih, kasur nyaman, dan variasi sarapannya lezat sekali. Anak-anak sangat betah!",
                ),
                (
                    "Bengkel Mobil & Servis Motor",
                    "Otomotif",
                    "casual",
                    5,
                    "Ulasan bengkel servis dengan fokus transparansi biaya servis, mekanik profesional dan jujur, pengerjaan tepat waktu, serta ruang tunggu yang nyaman.",
                    "mekanik jujur, estimasi harga transparan, pengerjaan rapi, ruang tunggu adem",
                    "Sangat puas servis di sini. Mekaniknya jujur dan komunikatif, estimasi biaya dijelaskan di awal tanpa biaya siluman. Pengerjaan rapi dan tepat waktu.",
                ),
                (
                    "Restoran Keluarga & Kuliner Nusantara",
                    "Kafe & Kuliner",
                    "family",
                    5,
                    "Ulasan restoran santap bersama keluarga dengan pujian kelezatan cita rasa otentik, porsi kenyang, area parkir mobil lapang, dan pelayanan gesit.",
                    "porsi pas, bumbu meresap, tempat parkir luas, cocok rombongan, harga bersahabat",
                    "Rekomendasi terbaik untuk makan bersama keluarga besar! Menunya lezat dengan bumbu yang kaya rasa. Area parkir luas dan stafnya sangat sigap melayani.",
                ),
                (
                    "International Traveler / Tourist",
                    "Hospitality",
                    "tourist",
                    5,
                    "International traveler review highlighting hospitality, clean facilities, English-speaking staff, and great atmosphere.",
                    "great hospitality, English speaking, clean facility, welcoming atmosphere, easy to find",
                    "Exceptional experience! The staff was very welcoming and spoke great English. Clean environment and authentic local vibes. Highly recommended for tourists!",
                ),
            ]
            conn.executemany(
                """INSERT INTO review_templates (title, category, persona, star_rating, prompt_template, keywords, sample_output)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                defaults,
            )


def get_review_templates():
    """Retrieve all saved review templates ordered by id DESC."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM review_templates ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def add_review_template(title, category, persona, star_rating, prompt_template, keywords="", sample_output=""):
    """Create a new review template preset."""
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO review_templates (title, category, persona, star_rating, prompt_template, keywords, sample_output)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, category, persona, int(star_rating or 5), prompt_template, keywords, sample_output),
        )
        return cur.lastrowid


def delete_review_template(template_id):
    """Delete a review template."""
    with get_db() as conn:
        conn.execute("DELETE FROM review_templates WHERE id = ?", (template_id,))


# ── Drip Campaign & Schedule Engine ───────────────────────────────────────────

def get_campaign_settings():
    """Get active campaign schedule settings."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM campaign_settings WHERE id = 1").fetchone()
        if not row:
            return {
                "drip_min_delay": 30,
                "drip_max_delay": 90,
                "active_hour_start": 8,
                "active_hour_end": 21,
                "anti_spam_jitter": 25,
                "is_paused": 0,
            }
        return dict(row)


def update_campaign_settings(drip_min_delay, drip_max_delay, active_hour_start, active_hour_end, anti_spam_jitter, is_paused=0):
    """Update drip campaign schedule parameters."""
    with get_db() as conn:
        conn.execute(
            """UPDATE campaign_settings 
               SET drip_min_delay = ?, drip_max_delay = ?, active_hour_start = ?, active_hour_end = ?, anti_spam_jitter = ?, is_paused = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = 1""",
            (
                max(5, int(drip_min_delay or 30)),
                max(int(drip_min_delay or 30), int(drip_max_delay or 90)),
                max(0, min(23, int(active_hour_start or 8))),
                max(0, min(23, int(active_hour_end or 21))),
                max(0, min(100, int(anti_spam_jitter or 25))),
                1 if is_paused else 0,
            ),
        )


def get_scheduled_queue_overview():
    """Retrieve all pending review jobs across all businesses and calculate smart drip timeline ETAs."""
    settings = get_campaign_settings()
    with get_db() as conn:
        query = """
            SELECT r.id, r.business_id, r.email_id, r.status, r.star_rating, r.review_type, r.review_language, r.created_at,
                   b.name AS business_name, b.url AS business_url,
                   e.email AS email_address, e.flagged AS email_flagged
            FROM reviews r
            JOIN businesses b ON r.business_id = b.id
            JOIN emails e ON r.email_id = e.id
            WHERE r.status = 'pending'
            ORDER BY r.id ASC
        """
        rows = conn.execute(query).fetchall()

    avg_delay_min = (settings.get("drip_min_delay", 30) + settings.get("drip_max_delay", 90)) / 2
    jitter = settings.get("anti_spam_jitter", 25) / 100.0
    active_start = settings.get("active_hour_start", 8)
    active_end = settings.get("active_hour_end", 21)
    is_paused = bool(settings.get("is_paused", 0))

    now = datetime.now()
    scheduled_items = []
    current_sim_time = now

    for index, r in enumerate(rows):
        item = dict(r)
        # Advance time by average delay with jitter variation
        variance = (1.0 + ((index % 5 - 2) * jitter * 0.5))
        delay_delta = timedelta(minutes=max(5, avg_delay_min * variance))
        current_sim_time += delay_delta

        # Adjust for operating hours (skip overnight hours)
        if current_sim_time.hour < active_start:
            current_sim_time = current_sim_time.replace(hour=active_start, minute=15)
        elif current_sim_time.hour >= active_end:
            current_sim_time = (current_sim_time + timedelta(days=1)).replace(hour=active_start, minute=15)

        item["estimated_run_at"] = current_sim_time.strftime("%Y-%m-%d %H:%M:%S")
        item["eta_minutes"] = max(1, int((current_sim_time - now).total_seconds() / 60))
        scheduled_items.append(item)

    # Calculate daily capacity
    active_hours_per_day = max(1, active_end - active_start) if active_end > active_start else 12
    daily_capacity = int((active_hours_per_day * 60) / max(10, avg_delay_min))

    return {
        "settings": settings,
        "is_paused": is_paused,
        "total_queued": len(scheduled_items),
        "daily_capacity": daily_capacity,
        "active_businesses_count": len(set(i["business_id"] for i in scheduled_items)),
        "queue": scheduled_items,
    }


def push_direct_review(business_id, email_id, star_rating, review_text, language="Indonesian"):
    """Directly insert a customized or generated review into pending queue for a specific business and account."""
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO reviews (business_id, email_id, star_rating, review_text, review_language, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (int(business_id), int(email_id), int(star_rating or 5), review_text, language),
        )
        return cur.lastrowid


def get_worker_system_status():
    """Retrieve detailed real-time worker and virtual display metrics."""
    with get_db() as conn:
        active_job = conn.execute("""
            SELECT r.id, r.star_rating, r.status, b.name AS business_name, e.email
            FROM reviews r
            JOIN businesses b ON r.business_id = b.id
            JOIN emails e ON r.email_id = e.id
            WHERE r.status = 'in_progress'
            LIMIT 1
        """).fetchone()

        recent_logs = conn.execute("""
            SELECT p.id, p.level, p.message, p.created_at, b.name AS business_name
            FROM process_logs p
            LEFT JOIN businesses b ON p.business_id = b.id
            ORDER BY p.id DESC
            LIMIT 80
        """).fetchall()

        total_pending = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'pending'").fetchone()[0]
        total_reviewed_today = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE status = 'reviewed' AND DATE(reviewed_at) = DATE('now')"
        ).fetchone()[0]
        total_failed_today = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE status = 'failed' AND DATE(created_at) = DATE('now')"
        ).fetchone()[0]

    return {
        "active_job": dict(active_job) if active_job else None,
        "recent_logs": [dict(l) for l in reversed(recent_logs)],
        "total_pending": total_pending,
        "total_reviewed_today": total_reviewed_today,
        "total_failed_today": total_failed_today,
    }


def create_user(username: str, password_hash: str, role: str = "user") -> bool:
    """Create a new registered user in the database."""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username.strip(), password_hash, role),
            )
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error creating user: {e}")
        return False


def get_user_by_username(username: str) -> Optional[dict]:
    """Retrieve user record by username (case-insensitive)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()
        if row:
            return dict(row)
        return None


def get_all_users() -> list:
    """Retrieve all registered users without exposing password hashes."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


