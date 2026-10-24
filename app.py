import csv
import io
import os
import random
import signal
import subprocess
import sys
from datetime import datetime, timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import db
import bot

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32).hex())
app.permanent_session_lifetime = timedelta(days=7)

# Hash is computed once at startup from the plaintext value in .env
_PASSWORD_HASH = generate_password_hash(
    os.environ.get("APP_PASSWORD", "changeme")
)

# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    error = False
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(_PASSWORD_HASH, password):
            session.permanent = True
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        error = True

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    businesses = db.get_all_businesses()
    all_emails = db.get_all_emails()
    all_cookies = db.get_all_cookies()
    with db.get_db() as conn:
        queue_metrics = conn.execute(
            "SELECT "
            "SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending, "
            "SUM(CASE WHEN status = 'reviewed' THEN 1 ELSE 0 END) AS reviewed, "
            "SUM(CASE WHEN status IN ('failed','flagged') THEN 1 ELSE 0 END) AS failed "
            "FROM reviews"
        ).fetchone()
    return render_template(
        "dashboard.html", businesses=businesses, all_emails=all_emails,
        all_cookies=all_cookies,
        eligible_emails=sum(1 for e in all_emails if not e.get("flagged")),
        flagged_emails=sum(1 for e in all_emails if e.get("flagged")),
        queue_metrics=dict(queue_metrics or {}),
    )


@app.route("/business/add", methods=["POST"])
@login_required
def add_business():
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    if name and url:
        db.add_business(name, url)
    return redirect(url_for("dashboard"))


@app.route("/business/<int:business_id>/delete", methods=["POST"])
@login_required
def delete_business(business_id):
    db.delete_business(business_id)
    return redirect(url_for("dashboard"))


# ── Business detail ───────────────────────────────────────────────────────────

@app.route("/business/<int:business_id>")
@login_required
def business(business_id):
    biz = db.get_business(business_id)
    if not biz:
        return redirect(url_for("dashboard"))
    reviews = db.get_reviews_for_business(business_id)
    config = db.get_review_config(business_id)
    is_running = any(r["status"] == "reviewing" for r in reviews)
    all_emails = db.get_all_emails()
    used_email_ids = {r["email_id"] for r in reviews}
    selectable_email_count = sum(1 for e in all_emails if e["id"] not in used_email_ids)
    total_pool = db.count_emails()
    already_queued = db.count_queued_for_business(business_id)
    already_reviewed = db.count_reviewed_for_business(business_id)
    return render_template(
        "business.html",
        business=biz,
        reviews=reviews,
        config=config,
        is_running=is_running,
        all_emails=all_emails,
        used_email_ids=used_email_ids,
        selectable_email_count=selectable_email_count,
        total_pool=total_pool,
        already_queued=already_queued,
        already_reviewed=already_reviewed,
    )


@app.route("/business/<int:business_id>/process-log")
@login_required
def process_log(business_id):
    """Polling endpoint for the live process-log panel."""
    if not db.get_business(business_id):
        return jsonify({"status": "error", "message": "Business not found"}), 404
    reviews = db.get_reviews_for_business(business_id)
    return jsonify({
        "status": "reviewing" if any(row["status"] == "reviewing" for row in reviews) else "idle",
        "logs": db.get_process_logs(business_id),
    })


@app.route("/business/<int:business_id>/inspect-review/<int:review_id>")
@login_required
def inspect_review(business_id, review_id):
    """Read-only check; it never edits or submits public content."""
    biz = db.get_business(business_id)
    review = db.get_review_for_business(review_id, business_id)
    if not biz or not review:
        return jsonify({"status": "error", "message": "Review tidak ditemukan."}), 404
    result = bot.inspect_existing_review(
        review["email"], biz["url"], biz["name"], review_id=review_id,
        business_id=business_id, star_rating=review.get("star_rating") or 5,
        review_prompt=biz.get("business_description") or "",
        review_type=review.get("review_type") or "medium",
        language=review.get("review_language") or "English",
        review_style=(db.get_review_config(business_id) or {}).get("review_style") or "random",
    )
    return jsonify(result)


@app.route("/business/<int:business_id>/chromium-preview.png")
@login_required
def chromium_preview(business_id):
    """Return a read-only snapshot of the virtual display used by Chromium."""
    if not db.get_business(business_id):
        return Response(status=404)
    try:
        capture = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "x11grab", "-video_size", "1366x768", "-i",
                os.environ.get("CHROMIUM_DISPLAY", ":99"),
                "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-",
            ],
            capture_output=True,
            timeout=8,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return Response("Preview Chromium belum tersedia.", status=503, mimetype="text/plain")

    return Response(
        capture.stdout,
        mimetype="image/png",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.route("/business/<int:business_id>/chromium-stream.mjpg")
@login_required
def chromium_stream(business_id):
    """Stream the Chromium virtual display as a live MJPEG preview."""
    if not db.get_business(business_id):
        return Response(status=404)

    display = os.environ.get("CHROMIUM_DISPLAY", ":99")

    def frames():
        process = subprocess.Popen(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "x11grab", "-framerate", "2", "-video_size", "1366x768",
                "-i", display, "-vf", "scale=960:-1", "-q:v", "7",
                "-f", "mpjpeg", "-boundary_tag", "frame", "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        try:
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
        finally:
            process.kill()
            process.wait()

    return Response(
        stream_with_context(frames()),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.route("/business/<int:business_id>/save-config", methods=["POST"])
@login_required
def save_config(business_id):
    config = {
        "business_description": "",
        "review_style": request.form.get("review_style", "random"),
        "star_1_count": 0,
        "star_2_count": 0,
        "star_3_count": 0,
        "star_4_count": 0,
        "star_5_count": 0,
        "delay_seconds": max(5, int(request.form.get("delay_seconds") or 60)),
    }
    db.save_review_config(business_id, config)
    return redirect(url_for("business", business_id=business_id, saved=1))


@app.route("/emails/sample-csv")
@login_required
def sample_csv():
    content = (
        "email,password,totp_secret\n"
        "example1@gmail.com,yourpassword1,\n"
        "example2@gmail.com,yourpassword2,JBSWY3DPEHPK3PXP\n"
    )
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_emails.csv"},
    )


# ── Google Cookies ────────────────────────────────────────────────────────────

@app.route("/cookies/add", methods=["POST"])
@login_required
def add_cookie():
    import json as _json
    email = request.form.get("cookie_email", "").strip()
    cookie_raw = request.form.get("cookie_json", "").strip()
    if not email or not cookie_raw:
        return redirect(url_for("dashboard", cookie_error="Email dan cookie tidak boleh kosong"))
    try:
        # Validate JSON
        _json.loads(cookie_raw)
    except Exception:
        return redirect(url_for("dashboard", cookie_error="Format cookie tidak valid (harus JSON)"))
    inserted = db.save_cookie(email, cookie_raw)

    # Otomatis masukkan ke email pool jika belum ada
    with db.get_db() as conn:
        existing = conn.execute("SELECT id FROM emails WHERE email = ?", (email,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO emails (email, password) VALUES (?, ?)", (email, "cookie_auth"))

    return redirect(url_for("dashboard", cookie_saved=1, cookie_new=1 if inserted else 0))


@app.route("/cookies/add-to-pool/<int:cookie_id>", methods=["POST"])
@login_required
def add_cookie_to_pool(cookie_id):
    with db.get_db() as conn:
        row = conn.execute("SELECT email FROM cookies WHERE id = ?", (cookie_id,)).fetchone()
        if row:
            email = row["email"]
            existing = conn.execute("SELECT id FROM emails WHERE email = ?", (email,)).fetchone()
            if not existing:
                conn.execute("INSERT INTO emails (email, password) VALUES (?, ?)", (email, "cookie_auth"))
    return redirect(url_for("dashboard"))


@app.route("/cookies/delete/<int:cookie_id>", methods=["POST"])
@login_required
def delete_cookie(cookie_id):
    db.delete_cookie(cookie_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
        return jsonify({"status": "ok", "message": "Cookie dihapus."})
    return redirect(url_for("dashboard"))


@app.route("/cookies/health")
@login_required
def cookie_health():
    """Return non-sensitive cookie metadata for dashboard polling."""
    import json as _json
    result = []
    for row in db.get_all_cookies():
        try:
            payload = _json.loads(row["cookie_json"])
            valid = isinstance(payload, list) and bool(payload) and all(
                isinstance(item, dict) and item.get("name") and item.get("value") is not None
                for item in payload
            )
            count = len(payload) if isinstance(payload, list) else 0
        except Exception:
            valid, count = False, 0
        result.append({"id": row["id"], "email": row["email"], "valid": valid,
                       "count": count, "updated_at": row["updated_at"]})
    return jsonify({"status": "ok", "checked_at": datetime.now().isoformat(timespec="seconds"), "cookies": result})


@app.route("/emails/<int:email_id>/unflag", methods=["POST"])
@login_required
def unflag_email(email_id):
    ok = db.unflag_email(email_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
        return jsonify({"status": "ok" if ok else "error"})
    return redirect(url_for("dashboard"))


# ── Global email pool ─────────────────────────────────────────────────────────

@app.route("/emails/upload", methods=["POST"])
@login_required
def upload_emails():
    import logging as _log
    csv_file = request.files.get("csv_file")
    inserted = 0
    updated = 0
    error_msg = None

    if csv_file and csv_file.filename:
        try:
            content = csv_file.read().decode("utf-8-sig")
            if not content.strip():
                error_msg = "File is empty"
            else:
                first_line = content.strip().split("\n")[0]
                if "User ID / Email Address" in first_line:
                    # G2G format (comma or tab separated)
                    delimiter = "\t" if "\t" in first_line else ","
                    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
                    for row in reader:
                        row = {k.strip(): (v or "").strip() for k, v in row.items()}
                        email = row.get("User ID / Email Address", "").lstrip("'")
                        password = row.get("Password", "")
                        secret_q = row.get("First Secret Question", "").lower()
                        totp_secret = row.get("First Secret Answer", "") if secret_q == "2fa" else None
                        totp_secret = totp_secret or None
                        if email and password:
                            result = db.add_email(email, password, totp_secret=totp_secret)
                            if result:
                                inserted += 1
                            else:
                                updated += 1
                else:
                    # Legacy format: email,password[,totp_secret]
                    reader = csv.DictReader(io.StringIO(content))
                    for row in reader:
                        email = (row.get("email") or "").strip()
                        password = (row.get("password") or "").strip()
                        totp_secret = (row.get("totp_secret") or "").strip() or None
                        if email and password:
                            result = db.add_email(email, password, totp_secret=totp_secret)
                            if result:
                                inserted += 1
                            else:
                                updated += 1
        except Exception as exc:
            _log.exception("CSV upload failed: %s", exc)
            error_msg = str(exc)
    else:
        error_msg = "No file selected"

    return redirect(url_for("dashboard", uploaded=inserted, updated=updated, upload_error=error_msg or ""))


@app.route("/emails/add", methods=["POST"])
@login_required
def add_email():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    totp_secret = request.form.get("totp_secret", "").strip() or None
    if email and password:
        db.add_email(email, password, totp_secret=totp_secret)
    return redirect(url_for("dashboard"))


@app.route("/emails/delete/<int:email_id>", methods=["POST"])
@login_required
def delete_email(email_id):
    db.delete_email(email_id)
    return redirect(url_for("dashboard"))


# ── Per-business review management ────────────────────────────────────────────

@app.route("/business/<int:business_id>/reset-review/<int:review_id>", methods=["POST"])
@login_required
def reset_review(business_id, review_id):
    db.reset_review(review_id)
    return redirect(url_for("business", business_id=business_id))


@app.route("/business/<int:business_id>/delete-review/<int:review_id>", methods=["POST"])
@login_required
def delete_review(business_id, review_id):
    db.delete_review(review_id)
    return redirect(url_for("business", business_id=business_id))


# ── Bot control ───────────────────────────────────────────────────────────────

@app.route("/business/<int:business_id>/start-bot", methods=["POST"])
@login_required
def start_bot(business_id):
    # The panel represents the current run, so discard stale messages first.
    db.clear_process_logs(business_id)
    # Optional email filter — if none submitted, use all
    selected_email_ids = request.form.getlist("selected_email_ids")
    allowed_email_ids = [int(x) for x in selected_email_ids if x.isdigit()] if selected_email_ids else None

    # Star counts come directly from the form
    star_list = []
    for star in range(1, 6):
        count = int(request.form.get(f"star_{star}_count") or 0)
        star_list.extend([star] * count)

    if not star_list:
        return jsonify({"status": "error", "message": "Select at least one star rating with a count > 0."})

    selected_language = request.form.get("selected_language", "Indonesian")
    if selected_language not in {"Indonesian", "English", "Spanish", "Chinese"}:
        selected_language = "Indonesian"
    language_list = [selected_language] * len(star_list)

    # Shuffle ratings and languages independently so assignments are random.
    random.shuffle(star_list)

    created, already_pending = db.create_review_jobs(business_id, star_list, language_list=language_list, allowed_email_ids=allowed_email_ids)
    if created == 0 and already_pending == 0:
        # Keep the reason explicit: an account may be connected/imported but
        # excluded from assignment after repeated failures.
        pool = db.get_all_emails()
        flagged = sum(1 for email in pool if email.get("flagged"))
        if pool and flagged == len(pool):
            message = (
                f"Tidak ada email yang dapat ditugaskan: {flagged} akun terhubung "
                "tetapi ditandai gagal setelah beberapa percobaan. Perbarui cookie "
                "atau tambahkan akun baru."
            )
        else:
            message = "No new emails available to assign."
        return jsonify({"status": "error", "message": message})

    db.add_process_log(
        business_id,
        f"{created} tugas review masuk ke antrean" + (f" ({already_pending} tugas sudah ada)." if already_pending else "."),
    )
    try:
        subprocess.Popen(
            [sys.executable, "worker.py", "--business-id", str(business_id)],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        db.add_process_log(business_id, "Worker langsung dijalankan untuk review baru.")
    except OSError as exc:
        db.add_process_log(business_id, f"Worker tidak dapat dijalankan: {exc}", level="error")
        return jsonify({"status": "error", "message": "Worker gagal dijalankan."}), 500

    return jsonify({"status": "processing", "jobs_created": created, "already_pending": already_pending})


@app.route("/business/<int:business_id>/stop-bot", methods=["POST"])
@login_required
def stop_bot(business_id):
    """Stop only this business's detached worker and recover its active job."""
    if not db.get_business(business_id):
        return jsonify({"status": "error", "message": "Business tidak ditemukan."}), 404

    stopped = 0
    ps = subprocess.run(
        ["ps", "-eo", "pid=,args="],
        capture_output=True,
        text=True,
        check=False,
    )
    marker = f"worker.py --business-id {business_id}"
    for line in ps.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or marker not in parts[1]:
            continue
        try:
            pid = int(parts[0])
            if pid == os.getpid():
                continue
            os.killpg(pid, signal.SIGTERM)
            stopped += 1
        except (ValueError, PermissionError, ProcessLookupError):
            continue

    deleted = db.delete_business_queue(business_id)
    db.add_process_log(
        business_id,
        f"Worker dihentikan. {deleted} tugas antrean dihapus; riwayat selesai dipertahankan.",
        level="warning",
    )
    return jsonify({"status": "stopped", "workers_stopped": stopped, "jobs_deleted": deleted})


if __name__ == "__main__":
    db.init_db()
    db.migrate_add_delay_seconds()
    db.migrate_add_review_type_language()
    db.migrate_add_totp_secret()
    db.migrate_add_email_fail_tracking()
    db.migrate_add_cookies_table()
    db.migrate_add_process_logs_table()
    #app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=5000, debug=False)
