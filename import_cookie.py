"""Safely import a browser-exported cookie JSON for the existing worker.

This script only validates and stores the cookie bundle in the local database.
It never opens a browser, posts content, or prints cookie values.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import db
import session_manager


def load_cookie_json(path: str | None) -> tuple[str, list[dict]]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    val = session_manager.validate_cookie_payload(raw)
    if not val.is_valid and val.status == session_manager.SessionStatus.INVALID:
        raise ValueError(val.reason)
    return raw, val.sanitized_cookies


def main() -> int:
    parser = argparse.ArgumentParser(description="Import cookie JSON for the review worker")
    parser.add_argument("--email", required=True, help="email akun yang memiliki cookie")
    parser.add_argument("--file", help="file JSON export cookie; jika kosong, baca stdin")
    parser.add_argument("--check-only", action="store_true", help="validasi tanpa menyimpan")
    args = parser.parse_args()
    try:
        cookie_json, cookies = load_cookie_json(args.file)
        if "@" not in args.email:
            raise ValueError("email akun tidak valid")
        val = session_manager.validate_cookie_payload(cookie_json)
        if not args.check_only:
            db.init_db()
            db.migrate_add_cookies_table()
            db.migrate_add_cookie_session_columns()
            db.save_cookie(args.email.strip(), cookie_json)
            db.update_cookie_session_status(args.email.strip(), val.status.value, val.reason)
        action = "valid" if args.check_only else "disimpan"
        print(f"Cookie {action}: akun={args.email.strip()} jumlah={len(cookies)} status={val.status.value}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Gagal import cookie: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
