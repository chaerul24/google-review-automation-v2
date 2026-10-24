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


def load_cookie_json(path: str | None) -> tuple[str, list[dict]]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    payload = json.loads(raw)
    if not isinstance(payload, list) or not payload:
        raise ValueError("cookie JSON harus berupa array yang tidak kosong")
    valid = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict) or not item.get("name") or item.get("value") is None:
            raise ValueError(f"cookie index {index} tidak memiliki name/value yang valid")
        valid.append(item)
    return json.dumps(valid, separators=(",", ":")), valid


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
        if not args.check_only:
            db.init_db()
            db.migrate_add_cookies_table()
            db.save_cookie(args.email.strip(), cookie_json)
        action = "valid" if args.check_only else "disimpan"
        print(f"Cookie {action}: akun={args.email.strip()} jumlah={len(cookies)}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Gagal import cookie: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
