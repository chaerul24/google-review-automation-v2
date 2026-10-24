import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = "reviews.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Google cookies per email (JSON dari browser)
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                cookie_json TEXT NOT NULL,
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
        conn.execute("INSERT INTO businesses (name, url) VALUES (?, ?)", (name, url))


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
            "SELECT * FROM emails ORDER BY created_at ASC"
        ).fetchall()
        return [dict(r) for r in rows]


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
    """
    with get_db() as conn:
        rows = conn.execute(
            """SELECT r.*, e.email, e.password, e.totp_secret
               FROM reviews r
               JOIN emails e ON e.id = r.email_id
               WHERE r.business_id = ? AND r.status = 'pending'
                 AND e.flagged = 0
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

    # Pad language_list with 'English' if shorter than star_list
    effective_langs = list(language_list or [])
    while len(effective_langs) < n:
        effective_langs.append('English')
    effective_langs = effective_langs[:n]

    with get_db() as conn:
        # Emails already assigned to this business with pending status
        pending_email_ids = {
            r["email_id"]
            for r in conn.execute(
                "SELECT email_id FROM reviews WHERE business_id = ? AND status = 'pending'",
                (business_id,),
            ).fetchall()
        }

        # Emails already assigned to this business (any status)
        used = {
            r["email_id"]
            for r in conn.execute(
                "SELECT email_id FROM reviews WHERE business_id = ?", (business_id,)
            ).fetchall()
        }

        # Pull enough fresh emails from the pool
        all_emails = conn.execute(
            "SELECT id FROM emails WHERE COALESCE(flagged, 0) = 0 ORDER BY created_at ASC"
        ).fetchall()
        available = [
            r["id"] for r in all_emails
            if r["id"] not in used
            and (allowed_email_ids is None or r["id"] in set(allowed_email_ids))
        ]

        count = 0
        for idx, (star, rtype, lang) in enumerate(zip(star_list, effective_types, effective_langs)):
            if idx >= len(available):
                break
            conn.execute(
                "INSERT INTO reviews (email_id, business_id, star_rating, review_type, review_language, status) "
                "VALUES (?, ?, ?, ?, ?, 'pending')",
                (available[idx], business_id, star, rtype, lang),
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
            """SELECT id, review_id, level, message, created_at
               FROM process_logs WHERE business_id = ?
               ORDER BY id DESC LIMIT ?""",
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
        return dict(row) if row else None


def save_review_config(business_id, config):
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
                    business_id,
                ),
            )
        else:
            conn.execute(
                """INSERT INTO review_configs
                       (business_id, business_description, review_style,
                        star_1_count, star_2_count, star_3_count, star_4_count, star_5_count,
                        delay_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                ),
            )


# ── Google Cookies ────────────────────────────────────────────────────────────

def get_all_cookies():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM cookies ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


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
        conn.execute("DELETE FROM cookies WHERE id = ?", (cookie_id,))


def migrate_add_cookies_table():
    """Create cookies table if it doesn't exist (safe to call multiple times)."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                cookie_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
