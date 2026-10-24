import hashlib
import logging
import os
import random
import time
import traceback

import pyotp

from dotenv import load_dotenv
from seleniumbase import sb_cdp
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import db
import json as _json
import re
import urllib.parse
load_dotenv()

log = logging.getLogger(__name__)

PROXY = os.environ.get("PROXY", "")
print(PROXY)

def get_fingerprint(email):
    """Generate a deterministic fingerprint based on the email address."""
    h = int(hashlib.md5(email.encode()).hexdigest(), 16)
    
    # 1. User Agents (Modern versions)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ]
    ua = user_agents[h % len(user_agents)]
    
    # 2. Resolutions
    resolutions = ["1920,1080", "1536,864", "1366,768", "1440,900", "1600,900"]
    res = resolutions[h % len(resolutions)]
    
    # 3. Hardware / Memory
    concurrency = [4, 8, 12, 16][h % 4]
    memory = [4, 8, 16][h % 3]
    
    return {
        "ua": ua,
        "res": res,
        "concurrency": concurrency,
        "memory": memory,
        "locale": "en-US"
    }


def generate_review(business_name, review_prompt, star_rating, review_type='medium', language='English', review_style='random'):
    if review_type == 'no_text':
        return ''

    templates = {
        'Indonesian': [
            f"Sangat puas berkunjung ke {business_name}. Tempatnya sangat nyaman, bersih, dan pelayanannya ramah. Sangat direkomendasikan!",
            f"Pengalaman luar biasa di {business_name}. Pelayanannya cepat dan memuaskan. Pasti akan kembali lagi ke sini.",
            f"Tempat yang luar biasa! {business_name} memberikan pelayanan dan kualitas terbaik. Sangat puas bintang 5.",
            f"Pelayanan di {business_name} sangat memuaskan, fasilitas rapi dan nyaman. Rekomendasi banget untuk siapa saja!"
        ],
        'English': [
            f"Outstanding experience at {business_name}! The service was prompt, friendly, and top notch. Highly recommended to everyone!",
            f"Had a wonderful time visiting {business_name}. Very clean, professional, and welcoming atmosphere. 5 stars all the way!",
            f"Truly impressed with the quality and great service at {business_name}. Will definitely be coming back again!",
            f"Great place! Everything at {business_name} was seamless and well organized. Highly satisfied with my visit."
        ]
    }
    lang_key = 'Indonesian' if str(language).lower() in ('indonesian', 'indonesia', 'id') else 'English'
    positive = templates.get(lang_key, templates['Indonesian'])
    negative = {
        'Indonesian': [
            f"Pengalaman di {business_name} kurang memuaskan. Pelayanannya perlu diperbaiki dan saya berharap kualitasnya bisa lebih baik.",
            f"Saya kecewa dengan kunjungan ke {business_name}. Prosesnya tidak nyaman dan hasilnya belum sesuai harapan.",
            f"Masih banyak hal yang perlu ditingkatkan di {business_name}, terutama pelayanan dan kenyamanan pelanggan."
        ],
        'English': [
            f"My experience at {business_name} was disappointing. The service needs improvement and the overall visit did not meet expectations.",
            f"I was not satisfied with my visit to {business_name}. The process was inconvenient and the result fell short of expectations.",
            f"There is still a lot to improve at {business_name}, especially the service and customer experience."
        ]
    }.get(lang_key, [])
    mode = review_style if review_style in ('baik', 'buruk') else random.choice(('baik', 'buruk'))
    return random.choice(positive if mode == 'baik' else negative)


def post_review(email, password, maps_url, star_rating, business_name, review_prompt, email_id, business_id, recovery_email=None, review_type='medium', language='English', review_style='random', totp_secret=None):
    safe_name = email.replace("@", "_at_").replace(".", "_")
    profile_dir = os.path.abspath(os.path.join("chrome_profiles", safe_name))
    os.makedirs(profile_dir, exist_ok=True)

    fp = get_fingerprint(email)
    iframe_sel = "iframe[name='goog-reviews-write-widget']"

    sb = None
    try:
        db.add_process_log(business_id, "Membuka browser Chromium.", email_id)
        chromium_args = [
            "--disable-sync",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-fre",
            "--disable-chrome-login-prompt",
        ]
        cookie_editor_dir = os.environ.get(
            "COOKIE_EDITOR_EXTENSION_DIR",
            os.path.join(
                os.environ.get("BROWSER_AUTOMATION_STORAGE", ""),
                "extensions",
                "cookie-editor",
            ),
        )
        if cookie_editor_dir and os.path.isfile(os.path.join(cookie_editor_dir, "manifest.json")):
            chromium_args.append(f"--load-extension={cookie_editor_dir}")
            db.add_process_log(business_id, "Extension Cookie-Editor dimuat ke Chromium.", email_id)
        sb = sb_cdp.Chrome(
            "https://accounts.google.com/signin/v2/identifier",
            headed=True,
            user_data_dir=profile_dir,
            proxy=PROXY,
            agent=fp["ua"],
            window_size=fp["res"],
            locale_code=fp["locale"],
            chromium_arg=",".join(chromium_args),
            disable_features="SigninIntercept,ChromeWhatsNewUI,AccountConsistency",
        )
        sb.maximize()
        # --- Try cookie login first ---
        sb.sleep(3)
        cookie_json = db.get_cookie_for_email(email)
        used_cookie = False
        if cookie_json:
            db.add_process_log(business_id, "Mencoba login dengan cookie Google.", email_id)
            log.info("Cookie found for %s -- injecting to skip login.", email)
            try:
                from mycdp import network as _cdp_net
                cookies_list = _json.loads(cookie_json)
                cookie_params = []
                for ck in cookies_list:
                    name = ck.get("name")
                    val = ck.get("value")
                    if not name or val is None:
                        continue
                    dom = ck.get("domain") or ".google.com"
                    path = ck.get("path") or "/"
                    sec = bool(ck.get("secure", True))
                    http_only = bool(ck.get("httpOnly", False))
                    ss = None
                    ss_val = str(ck.get("sameSite", "")).lower()
                    if ss_val == "strict":
                        ss = _cdp_net.CookieSameSite.STRICT
                    elif ss_val == "lax":
                        ss = _cdp_net.CookieSameSite.LAX
                    elif ss_val in ("none", "no_restriction"):
                        ss = _cdp_net.CookieSameSite.NONE

                    param = _cdp_net.CookieParam(
                        name=name,
                        value=str(val),
                        domain=dom,
                        path=path,
                        secure=sec,
                        http_only=http_only,
                        same_site=ss,
                    )
                    cookie_params.append(param)

                if not cookie_params:
                    raise ValueError("Cookie JSON tidak berisi cookie valid")

                # Do not mix a newly imported Cookie-Editor session with
                # cookies left in the account's persistent Chromium profile.
                # This only clears browser cookies; it does not delete the
                # profile, saved settings, or the database record.
                try:
                    sb.delete_all_cookies()
                except Exception:
                    log.debug("Could not clear existing browser cookies", exc_info=True)
                sb.get("https://www.google.com")
                sb.sleep(2)
                sb.set_all_cookies(cookie_params)
                sb.sleep(2)
                sb.get("https://myaccount.google.com/?hl=en")
                sb.sleep(6)
                cur = sb.get_current_url()
                if "myaccount.google.com" in cur or "/u/" in cur:
                    # Google renders the account identity dynamically. Read
                    # both visible text and identity-bearing DOM attributes;
                    # SeleniumBase get_text alone can miss those attributes.
                    identity_blob = sb.execute_script("""
                        const body = document.body ? document.body.innerText : '';
                        const nodes = [...document.querySelectorAll('[data-email],[aria-label],[title]')];
                        const attrs = nodes.map(n => [n.getAttribute('data-email'), n.getAttribute('aria-label'), n.getAttribute('title')].filter(Boolean).join(' '));
                        return body + '\\n' + attrs.join('\\n');
                    """) or ""
                    expected_visible = email.casefold() in str(identity_blob).casefold()
                    if expected_visible:
                        log.info("Cookie login OK; Google account detected: %s", email)
                        used_cookie = True
                        db.add_process_log(
                            business_id,
                            f"Login cookie berhasil. Akun Google terdeteksi: {email}.",
                            email_id,
                        )
                    else:
                        log.warning("Cookie reached account page but expected account was not visible for %s", email)
                        db.add_process_log(
                            business_id,
                            "Cookie masuk, tetapi nama/email akun Google tidak terverifikasi.",
                            email_id,
                            "warning",
                        )
                else:
                    log.warning("Cookie login failed for %s (url: %s), falling back to password", email, cur)
            except Exception as e:
                log.warning("Cookie inject error for %s: %s", email, e)

        # A supplied cookie is authoritative: never fall back to typing
        # credentials when its session cannot be verified.
        if cookie_json and not used_cookie:
            raise RuntimeError(
                "Cookie tersedia tetapi sesi akun Google tidak terverifikasi; "
                "perbarui cookie secara manual."
            )

        # --- Password login fallback (only when no cookie was supplied) ---
        if not used_cookie:
            db.add_process_log(business_id, "Login dengan kredensial akun Google.", email_id)
            sb.sleep(5)
            cur = sb.get_current_url()
            if "accounts.google.com" in cur:
                sb.sleep(2)
                sb.click('input[aria-label="Email or phone"]', timeout=15)
                sb.sleep(3)
                sb.type('input[aria-label="Email or phone"]', email, timeout=15)
                sb.sleep(3)
                sb.click("#identifierNext", timeout=15)
                sb.sleep(5)
                sb.click('input[type="password"]', timeout=30)
                sb.sleep(3)
                sb.type('input[type="password"]', password, timeout=30)
                sb.sleep(3)
                sb.click("#passwordNext", timeout=15)
                sb.sleep(5)

                try:
                    sb.wait_for_element_visible('input[name="totpPin"]', timeout=20)
                    totp_code = pyotp.TOTP(totp_secret).now() if totp_secret else ""
                    sb.click('input[name="totpPin"]', timeout=10)
                    sb.sleep(3)
                    sb.type('input[name="totpPin"]', totp_code, timeout=10)
                    sb.sleep(3)
                    sb.click("#totpNext", timeout=15)
                    sb.sleep(5)
                except Exception:
                    pass
                try:
                    sb.sleep(random.uniform(3, 6))
                    current_url = sb.get_current_url()
                    english_url = re.sub(r'([?&]hl=)[^&]+', r'\1en', current_url)
                    english_url = re.sub(r'hl%3D[^%&]+', 'hl%3Den', english_url)
                    if "hl=" not in urllib.parse.unquote(english_url):
                        separator = "&" if "?" in english_url else "?"
                        english_url += f"{separator}hl=en"
                    sb.get(english_url)
                    sb.sleep(random.uniform(5, 10))
                    sb.click_if_visible('button[aria-label="Cancel"]', timeout=10)
                    sb.sleep(3)
                    sb.click_if_visible('button[aria-label="Skip"]', timeout=10)
                except Exception:
                    pass

        # --- Navigate to Maps listing ---
        db.add_process_log(business_id, "Membuka halaman Google Maps.", email_id)
        sb.sleep(random.uniform(5, 8))
        sep = "&" if "?" in maps_url else "?"
        target_maps_url = maps_url if "hl=" in maps_url else f"{maps_url}{sep}hl=en"
        sb.get(target_maps_url)
        sb.sleep(random.uniform(8, 12))

        # Check if URL lost the place or empty, fallback to search query
        cur_url = sb.get_current_url()
        if "place//@" in cur_url or "google.com/maps/@" in cur_url:
            log.warning("Maps URL lost place, falling back to search query for: %s", business_name)
            fallback_url = f"https://maps.google.com/?q={urllib.parse.quote(business_name)}&hl=en"
            sb.get(fallback_url)
            sb.sleep(random.uniform(8, 12))

        # Dismiss any consent dialog if present
        for consent_btn in ['button:contains("Accept all")', 'button:contains("I agree")', 'button:contains("Setuju")']:
            try:
                if sb.is_element_visible(consent_btn):
                    sb.click(consent_btn)
                    sb.sleep(3)
            except Exception:
                pass

        # Try to click "Write a review" directly or open Reviews tab first
        write_clicked = False
        for wr_sel in [
            'button[aria-label="Write a review"]',
            'button[aria-label*="Write a review"]',
            'button[aria-label*="Tulis ulasan"]',
            'button:contains("Write a review")',
            'button:contains("Tulis ulasan")'
        ]:
            try:
                if sb.is_element_visible(wr_sel):
                    sb.click(wr_sel)
                    write_clicked = True
                    log.info("Clicked write review button via %s", wr_sel)
                    break
            except Exception:
                pass

        if not write_clicked:
            for rev_tab in [
                'button[aria-label*="Reviews"]',
                'button[aria-label*="Ulasan"]',
                'button[role="tab"][data-tab-index="1"]',
                'div[role="tablist"] button:nth-child(2)'
            ]:
                try:
                    if sb.is_element_visible(rev_tab):
                        sb.click(rev_tab)
                        log.info("Clicked reviews tab via %s", rev_tab)
                        sb.sleep(random.uniform(4, 7))
                        break
                except Exception:
                    pass

            for wr_sel in [
                'button[aria-label="Write a review"]',
                'button[aria-label*="Write a review"]',
                'button[aria-label*="Tulis ulasan"]',
                'button:contains("Write a review")',
                'button:contains("Tulis ulasan")'
            ]:
                try:
                    sb.click(wr_sel, timeout=15)
                    write_clicked = True
                    log.info("Clicked write review button via %s", wr_sel)
                    break
                except Exception:
                    pass

        sb.sleep(random.uniform(4, 8))

        # --- Confirm the review iframe is open before generating text ---
        sb.wait_for_element_visible(iframe_sel, timeout=30)
        db.add_process_log(business_id, "Form review Google Maps sudah terbuka.", email_id)
        sb.sleep(5)  # Brief wait before polling for the textarea

        # Wait for the textarea inside the iframe to become available (up to 60s)
        review_area = None
        for _attempt in range(24):  # 24 × 2.5s = 60s max
            review_area = sb.get_nested_element(iframe_sel, 'textarea[aria-label="Enter review"]')
            if review_area is not None:
                break
            log.debug("Waiting for review textarea (attempt %d/24)...", _attempt + 1)
            time.sleep(2.5)
        if review_area is None:
            raise RuntimeError("Review textarea never appeared inside iframe after 60s")

        review_area.click()  # Focus the textarea to ensure it's ready for input
        time.sleep(3)

        # Select the star rating before creating the local review text
        sb.nested_click(iframe_sel, f"div[data-rating='{star_rating}'][role='radio']")
        sb.sleep(random.uniform(2, 5))

        # Generate review text now that we know the write box is open and star is selected
        db.add_process_log(business_id, "Membuat teks dan memilih rating review.", email_id)
        review_text = generate_review(business_name, review_prompt, star_rating, review_type, language, review_style)
        log.info("Review generated for %s (type=%s, lang=%s)", email, review_type, language)

        # Type review text into the textarea inside the iframe (skip for no_text reviews)
        if review_text:
            review_area = sb.get_nested_element(iframe_sel, 'textarea[aria-label="Enter review"]')
            if review_area is None:
                raise RuntimeError("Could not find review textarea inside iframe")
            review_area.type(review_text)
            sb.sleep(random.uniform(2, 5))

        # Click the Post button inside the iframe by text content (stable, no dynamic attributes)
        db.add_process_log(business_id, "Mengirim review ke Google Maps.", email_id)
        sb.evaluate("""
            var iframe = document.querySelector("iframe[name='goog-reviews-write-widget']");
            var doc = iframe.contentDocument || iframe.contentWindow.document;
            var buttons = doc.querySelectorAll('button');
            for (var btn of buttons) {
                if (btn.textContent.trim() === 'Post') { btn.click(); break; }
            }
        """)
        sb.sleep(random.uniform(3, 5))

        # Click Done (also inside the iframe)
        sb.nested_click(iframe_sel, 'button[aria-label="Done"]')
        sb.sleep(random.uniform(3, 5))
        db.update_review_status(email_id, "reviewed", review_text, star_rating)
        log.info("Review posted successfully for %s", email)
        db.add_process_log(business_id, "Review berhasil dikirim.", email_id, "success")
        return True

    except Exception as exc:
        log.error("post_review failed for %s: %s", email, exc)
        log.error(traceback.format_exc())
        db.update_review_status(email_id, "pending", None, star_rating)
        db.add_process_log(business_id, f"Proses gagal: {str(exc)[:240]}", email_id, "error")
        return False

    finally:
        if sb is not None:
            sb.driver.stop()


def inspect_existing_review(email, maps_url, business_name, review_id=None, business_id=None,
                            star_rating=5, review_prompt="", review_type="medium",
                            language="English", review_style="random"):
    """Read-only inspection of the signed-in account's Maps review.

    This function never clicks a review form or submits/deletes public content.
    It relies on the account's existing profile session and reports unknown when
    Google does not expose enough information.
    """
    safe_name = email.replace("@", "_at_").replace(".", "_")
    profile_dir = os.path.abspath(os.path.join("chrome_profiles", safe_name))
    fp = get_fingerprint(email)
    sb = None
    try:
        target = maps_url if "hl=" in maps_url else f"{maps_url}{'&' if '?' in maps_url else '?'}hl=en"
        sb = sb_cdp.Chrome(
            target, headed=True, user_data_dir=profile_dir, proxy=PROXY,
            agent=fp["ua"], window_size=fp["res"], locale_code=fp["locale"],
            chromium_arg="--no-first-run,--no-default-browser-check,--disable-default-apps",
        )
        sb.sleep(5)
        current = sb.get_current_url()
        if "accounts.google.com" in current:
            return {"status": "unknown", "message": "Sesi akun belum login; buka Maps dan login secara manual."}
        body = sb.get_text("body") or ""
        markers = ("Your review", "Your Review", "Ulasan Anda", "Your rating")
        marker = next((m for m in markers if m in body), None)
        old_text = None
        if marker:
            pos = body.find(marker)
            old_text = " ".join(body[max(0, pos):pos + 600].split())
            status = "available"
            message = "Ulasan sudah tersedia."
        else:
            status = "not_found"
            message = "Belum ada ulasan yang terdeteksi pada halaman ini."
        preview = generate_review(business_name, review_prompt, star_rating, review_type, language, review_style)
        return {"status": status, "message": message, "old_text": old_text, "new_preview": preview,
                "manual_url": target}
    except Exception as exc:
        log.warning("Read-only review inspection failed for %s: %s", email, exc)
        return {"status": "unknown", "message": f"Tidak dapat memverifikasi ulasan: {str(exc)[:180]}"}
    finally:
        if sb is not None:
            sb.driver.stop()


def run_reviews(business_id, biz, config, delay=60):
    pending = db.get_pending_reviews(business_id)
    previous_email = None

    for index, review_row in enumerate(pending):
        star = review_row["star_rating"] or 5

        # Mark as in-progress
        db.update_review_status(review_row["id"], "reviewing", None, star)
        db.add_process_log(business_id, "Memulai proses review untuk akun yang dipilih.", review_row["id"])

        # Post the review via Selenium (review text generated inside, only when write box is open)
        log.info("Opening browser for %s", review_row["email"])
        success = post_review(
            review_row["email"],
            review_row["password"],
            biz["url"],
            star,
            biz["name"],
            config.get("business_description", ""),
            review_row["id"],
            business_id,
            recovery_email=previous_email,
            review_type=review_row.get("review_type") or "medium",
            language=review_row.get("review_language") or "English",
            review_style=config.get("review_style") or "random",
            totp_secret=review_row.get("totp_secret"),
        )
        if not success:
            log.warning("post_review returned False for %s", review_row["email"])
            flagged = db.increment_email_fail_count(review_row["email_id"])
            if flagged:
                log.warning(
                    "Email %s has failed 5 times — flagged and removed from all pending jobs.",
                    review_row["email"],
                )
        previous_email = review_row["email"]

        # Do not add an unnecessary wait after the final task.  For a
        # subsequent task, keep the configured safety delay and expose the
        # remaining time in the live process log so the UI is not ambiguous.
        if index < len(pending) - 1:
            actual_delay = max(1, int(round(random.uniform(delay, delay + 300))))
            db.add_process_log(
                business_id,
                f"Menunggu {actual_delay} detik sebelum review berikutnya.",
            )
            log.info("Waiting %ss before next review...", actual_delay)
            remaining = actual_delay
            while remaining > 0:
                step = min(5 if remaining > 5 else 1, remaining)
                time.sleep(step)
                remaining -= step
                if remaining <= 5:
                    db.add_process_log(
                        business_id,
                        f"Countdown review berikutnya: {remaining} detik.",
                    )
