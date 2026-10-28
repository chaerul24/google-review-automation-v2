"""Cookie-Based Chromium Session Manager for AutoBotix and Google Review Automation.

This module provides authorized, cookie-based Chromium session management without
attempting credential login (email/password/TOTP), MFA bypass, or CAPTCHA solving.
All operations are non-destructive and sanitize logs to protect session secrets.
"""

from __future__ import annotations

import ast
import fcntl
import json
import logging
import os
import re
import signal
import subprocess
import time
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

import db

log = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    NEEDS_LOGIN = "needs_login"
    INVALID = "invalid"
    DOMAIN_MISMATCH = "domain_mismatch"
    PROFILE_LOCKED = "profile_locked"
    MISSING_COOKIE = "missing_cookie"


class SessionError(Exception):
    """Base exception for session management errors."""

    def __init__(self, message: str, status: SessionStatus = SessionStatus.INVALID):
        super().__init__(message)
        self.status = status


class ProfileLockedError(SessionError):
    """Raised when a profile directory is already open in another process."""

    def __init__(self, message: str):
        super().__init__(message, status=SessionStatus.PROFILE_LOCKED)


class CookieValidationError(SessionError):
    """Raised when cookie data structure is malformed or invalid."""

    def __init__(self, message: str, status: SessionStatus = SessionStatus.INVALID):
        super().__init__(message, status=status)


@dataclass
class CookieValidationResult:
    is_valid: bool
    status: SessionStatus
    reason: str
    cookie_count: int
    cookie_names: list[str] = field(default_factory=list)
    sanitized_cookies: list[dict] = field(default_factory=list)
    detected_email: str | None = None
    normalized_json: str = field(default="")

    def to_dict(self) -> dict[str, Any]:
        """Return non-sensitive metadata safe for logs and dashboard."""
        return {
            "is_valid": self.is_valid,
            "status": self.status.value,
            "reason": self.reason,
            "cookie_count": self.cookie_count,
            "cookie_names": self.cookie_names,
            "detected_email": self.detected_email,
        }


def force_close_profile_processes(profile_dir: Path | str) -> int:
    """Terminate any Chromium or background processes currently holding this profile dir,
    then clean up stale lock files so that new sessions can enter cleanly.
    """
    p_dir = Path(profile_dir).resolve()
    dir_name = p_dir.name
    killed_count = 0

    # 1. Kill by PID recorded in .session_profile.lock
    lock_file = p_dir / ".session_profile.lock"
    if lock_file.exists():
        try:
            content = lock_file.read_text(errors="ignore")
            for line in content.splitlines():
                if line.startswith("pid="):
                    pid_str = line.split("=")[1].strip()
                    if pid_str.isdigit():
                        pid = int(pid_str)
                        if pid != os.getpid() and pid > 1:
                            try:
                                os.kill(pid, signal.SIGTERM)
                                killed_count += 1
                            except OSError:
                                pass
        except Exception:
            pass

    # 2. Kill Chromium processes with matching --user-data-dir
    if os.name != "nt":
        try:
            res = subprocess.run(
                ["pkill", "-9", "-f", f"user-data-dir=.*{dir_name}"],
                capture_output=True,
                timeout=3,
            )
            if res.returncode == 0:
                killed_count += 1
        except Exception:
            pass

    # 3. Clean up lock and singleton files
    time.sleep(0.5)
    for fname in (".session_profile.lock", "SingletonLock", "SingletonSocket", "SingletonCookie"):
        f_path = p_dir / fname
        if f_path.exists() or f_path.is_symlink():
            try:
                f_path.unlink(missing_ok=True)
            except Exception:
                pass

    return killed_count


class ProfileLock:
    """Non-blocking flock lock on a Chromium profile directory with auto force-close fallback."""

    def __init__(self, profile_dir: str | Path):
        self.profile_dir = Path(profile_dir).resolve()
        self.lock_path = self.profile_dir / ".session_profile.lock"
        self._fd: Any | None = None

    def acquire(self, force: bool = True) -> None:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._fd = open(self.lock_path, "a+")
        try:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._fd.seek(0)
            self._fd.truncate()
            self._fd.write(f"pid={os.getpid()}\ntime={time.time()}\n")
            self._fd.flush()
        except (BlockingIOError, OSError) as exc:
            if self._fd is not None:
                try:
                    self._fd.close()
                except Exception:
                    pass
                self._fd = None

            if force:
                log.info("Profile '%s' is locked. Force-closing existing Chromium processes and re-acquiring...", self.profile_dir.name)
                force_close_profile_processes(self.profile_dir)
                time.sleep(1.0)
                self._fd = open(self.lock_path, "a+")
                try:
                    fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._fd.seek(0)
                    self._fd.truncate()
                    self._fd.write(f"pid={os.getpid()}\ntime={time.time()}\n")
                    self._fd.flush()
                    return
                except (BlockingIOError, OSError) as retry_exc:
                    if self._fd is not None:
                        try:
                            self._fd.close()
                        except Exception:
                            pass
                        self._fd = None
                    raise ProfileLockedError(
                        f"Direktori profil '{self.profile_dir.name}' masih terkunci setelah mencoba menutup proses sebelumnya."
                    ) from retry_exc

            raise ProfileLockedError(
                f"Direktori profil '{self.profile_dir.name}' sedang digunakan oleh proses lain."
            ) from exc

    def release(self) -> None:
        if self._fd is not None:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
                self._fd.close()
            except Exception:
                pass
            finally:
                self._fd = None

    def is_locked(self) -> bool:
        """Check if profile is currently locked by another process without holding lock."""
        if not self.lock_path.exists():
            return False
        try:
            test_fd = open(self.lock_path, "a+")
            try:
                fcntl.flock(test_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(test_fd.fileno(), fcntl.LOCK_UN)
                return False
            finally:
                test_fd.close()
        except (BlockingIOError, OSError):
            return True

    def __enter__(self) -> ProfileLock:
        self.acquire(force=True)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()


def get_profile_dir(account_id_or_email: str, base_dir: str | Path = "chrome_profiles") -> Path:
    """Return persistent, sanitized profile directory for an account."""
    safe_name = account_id_or_email.replace("@", "_at_").replace(".", "_")
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", safe_name)
    path = Path(base_dir).resolve() / safe_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_domain(url: str) -> str:
    """Extract clean domain name without scheme, port, or path."""
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    host = parsed.hostname or ""
    return host.lower()


def domain_matches(cookie_domain: str, target_domain: str) -> bool:
    """Verify if a cookie domain matches target domain according to standard rules."""
    c_dom = cookie_domain.strip().lower().lstrip(".")
    t_dom = target_domain.strip().lower().lstrip(".")
    if not c_dom or not t_dom:
        return False
    if c_dom == t_dom:
        return True
    if t_dom.endswith("." + c_dom):
        return True
    if c_dom.endswith("." + t_dom):
        return True
    return False


def extract_email_from_text(text: Any) -> str | None:
    """Safely extract valid email address from any string or cookie value."""
    if not text:
        return None
    try:
        unquoted = urllib.parse.unquote(str(text))
    except Exception:
        unquoted = str(text)
    # Strip common Google prefixes like AF_QU_...# or AF_QU_
    cleaned = re.sub(r'^[A-Za-z0-9_-]+[#_]', '', unquoted)
    m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', cleaned)
    if m:
        candidate = m.group(0).strip().lower()
        if "." in candidate.split("@")[-1]:
            return candidate
    return None


def parse_cookie_payload(
    raw_payload: Any,
    target_domain: str | None = None,
) -> tuple[list[dict], str | None, str | None]:
    """Parse and normalize cookies from various formats:
    - JSON Array of cookie objects (Cookie-Editor, EditThisCookie, J2Team)
    - JSON Object with 'cookies', 'data', or 'items' array
    - Single cookie dict: {"name": "...", "value": "..."}
    - Key-value JSON map: {"SID": "...", "HSID": "..."}
    - Python stringified dict/list (single quotes)
    - Markdown code-fenced string (```json ... ```)
    - Netscape / cookies.txt tab-separated format
    - Raw HTTP Cookie Header string (SID=...; HSID=...) or cURL Cookie format
    - URL-encoded cookie string

    Returns:
        (sanitized_items_list, detected_email, error_reason_if_any)
    """
    if raw_payload is None:
        return [], None, "Payload cookie kosong."

    if isinstance(raw_payload, str) and not raw_payload.strip():
        return [], None, "Payload cookie kosong."

    clean_target = extract_domain(target_domain) if target_domain else "google.com"
    default_domain = f".{clean_target}" if clean_target else ".google.com"

    email_found: str | None = None
    items_raw: Any = None

    if isinstance(raw_payload, (list, dict)):
        items_raw = raw_payload
    else:
        text = str(raw_payload).strip()
        # 1. Strip markdown fences (```json ... ``` or ``` ...)
        text = re.sub(r"^```(?:json|json5|text|bash)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        # 2. Strip 'Cookie: ' or 'cookie: ' prefix
        if text.lower().startswith("cookie:"):
            text = text[7:].strip()

        # 3. URL decode if needed (%5B is '[', %7B is '{')
        if text.startswith("%5B") or text.startswith("%7B") or "%22" in text:
            try:
                text = urllib.parse.unquote(text)
            except Exception:
                pass

        # 4. Direct JSON parsing
        try:
            items_raw = json.loads(text)
        except Exception:
            pass

        # 5. Try fixing trailing commas before ] or }
        if items_raw is None:
            try:
                cleaned = re.sub(r",\s*([\]}])", r"\1", text)
                items_raw = json.loads(cleaned)
            except Exception:
                pass

        # 6. Try Python ast.literal_eval for single quotes or Python syntax
        if items_raw is None:
            try:
                eval_text = re.sub(r"\btrue\b", "True", text, flags=re.IGNORECASE)
                eval_text = re.sub(r"\bfalse\b", "False", eval_text, flags=re.IGNORECASE)
                eval_text = re.sub(r"\bnull\b", "None", eval_text, flags=re.IGNORECASE)
                evaluated = ast.literal_eval(eval_text)
                if isinstance(evaluated, (list, dict)):
                    items_raw = evaluated
            except Exception:
                pass

        # 7. Check Netscape / cookies.txt format
        if items_raw is None:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            has_tabs = any("\t" in l for l in lines)
            if has_tabs or any(l.startswith("#HttpOnly_") or l.startswith(".google.com") or l.startswith("google.com") for l in lines):
                netscape_items = []
                for line in lines:
                    if line.startswith("#") and not line.startswith("#HttpOnly_"):
                        continue
                    parts = re.split(r"\t+|\s{2,}", line)
                    if len(parts) >= 6:
                        domain = parts[0].replace("#HttpOnly_", "")
                        http_only = parts[0].startswith("#HttpOnly_")
                        path = parts[2]
                        secure = parts[3].upper() == "TRUE"
                        expiry = None
                        if len(parts) > 4:
                            try:
                                expiry = float(parts[4])
                            except ValueError:
                                pass
                        name = parts[5]
                        val = parts[6] if len(parts) > 6 else ""
                        netscape_items.append({
                            "name": name,
                            "value": val,
                            "domain": domain,
                            "path": path,
                            "secure": secure,
                            "httpOnly": http_only,
                            "expiry": expiry,
                        })
                if netscape_items:
                    items_raw = netscape_items

        # 8. Raw HTTP Cookie Header format (e.g. SID=abc; HSID=def) or newline-separated pairs
        if items_raw is None:
            header_items = []
            tokens = re.split(r"[;\r\n]+", text)
            standard_directives = {"path", "domain", "expires", "max-age", "samesite", "httponly", "secure", "priority"}
            for token in tokens:
                token = token.strip()
                if "=" in token:
                    k, _, v = token.partition("=")
                    k = k.strip()
                    v = v.strip()
                    if k and k.lower() not in standard_directives:
                        header_items.append({
                            "name": k,
                            "value": v,
                            "domain": default_domain,
                            "path": "/",
                            "secure": True,
                        })
            if header_items:
                items_raw = header_items

    # 9. Extract list from items_raw
    if items_raw is None:
        return [], None, "Format cookie tidak dikenali. Gunakan JSON array, format Cookie-Editor, Netscape, atau string header."

    if isinstance(items_raw, dict):
        if "cookies" in items_raw and isinstance(items_raw["cookies"], list):
            items_list = items_raw["cookies"]
        elif "data" in items_raw and isinstance(items_raw["data"], list):
            items_list = items_raw["data"]
        elif "items" in items_raw and isinstance(items_raw["items"], list):
            items_list = items_raw["items"]
        elif "name" in items_raw and "value" in items_raw:
            items_list = [items_raw]
        else:
            # Key-value map: {"SID": "...", "HSID": "..."}
            items_list = [
                {"name": k, "value": str(v), "domain": default_domain, "path": "/", "secure": True}
                for k, v in items_raw.items()
                if isinstance(k, str) and not isinstance(v, (dict, list))
            ]
    elif isinstance(items_raw, list):
        items_list = items_raw
    else:
        return [], None, "Format data cookie bukan array, objek, atau daftar cookie yang valid."

    if not items_list:
        return [], None, "Daftar cookie kosong."

    sanitized_items = []
    for idx, item in enumerate(items_list):
        if not isinstance(item, dict):
            continue
        raw_name = item.get("name")
        if not raw_name or not str(raw_name).strip():
            continue
        name = str(raw_name).strip()
        val = str(item.get("value") if item.get("value") is not None else "")

        # Try to detect email
        if not email_found:
            cand = extract_email_from_text(val)
            if cand:
                email_found = cand
            if not email_found:
                cand = extract_email_from_text(name)
                if cand:
                    email_found = cand

        domain = str(item.get("domain") or "").strip()
        if not domain:
            domain = default_domain

        path = str(item.get("path") or "/").strip()
        secure = bool(item.get("secure", True))
        http_only = bool(item.get("httpOnly", False))

        same_site_raw = str(item.get("sameSite") or "").strip().lower()
        if same_site_raw in ("strict", "lax", "none", "no_restriction"):
            same_site = "None" if same_site_raw == "no_restriction" else same_site_raw.capitalize()
        else:
            same_site = None

        expiry_raw = item.get("expirationDate") or item.get("expiry") or item.get("expires")
        expiry_ts = None
        if expiry_raw is not None:
            try:
                expiry_ts = float(expiry_raw)
            except (ValueError, TypeError):
                pass

        # Auto-extend Google cookies so they do not expire prematurely
        google_core_names = (
            "sid", "hsid", "ssid", "apisid", "sapisid",
            "__secure-1psid", "__secure-3psid", "__secure-1psidts", "__secure-3psidts",
            "login_info", "nid", "1p_jar"
        )
        now_curr = time.time()
        if name.lower() in google_core_names:
            # If expiry is missing, in the past, or expires within 60 days, extend to 2 years
            if expiry_ts is None or expiry_ts < now_curr + (60 * 86400):
                expiry_ts = now_curr + (730 * 86400)  # 2 years in future

        sanitized_items.append({
            "name": name,
            "value": val,
            "domain": domain,
            "path": path,
            "secure": secure,
            "httpOnly": http_only,
            "sameSite": same_site,
            "expiry": expiry_ts,
        })

    if not sanitized_items:
        return [], None, "Tidak ada entri cookie yang valid dalam payload."

    return sanitized_items, email_found, None


def validate_cookie_payload(
    raw_payload: str | list | dict,
    target_domain: str | None = None,
    now_ts: float | None = None,
) -> CookieValidationResult:
    """Validate structure, expiry, and domain applicability of a cookie set.
    
    Ensures no sensitive cookie values are emitted into the result metadata.
    """
    now = now_ts if now_ts is not None else time.time()
    clean_target = extract_domain(target_domain) if target_domain else None

    sanitized_items, detected_email, error_reason = parse_cookie_payload(
        raw_payload, target_domain=target_domain
    )

    if error_reason or not sanitized_items:
        return CookieValidationResult(
            is_valid=False,
            status=SessionStatus.INVALID,
            reason=error_reason or "Payload cookie kosong atau tidak valid.",
            cookie_count=0,
            detected_email=detected_email,
        )

    sanitized_cookies: list[dict] = []
    cookie_names: list[str] = []
    expired_count = 0
    timestamped_count = 0
    domain_matched_count = 0

    # Key authentication tokens that imply session validity
    core_auth_names = {
        "sid", "hsid", "ssid", "apisid", "sapisid", "__secure-1psid",
        "__secure-3psid", "session", "sessionid", "token", "auth_token",
        "connect.sid", "remember_token", "jwt",
    }
    core_auth_present = False
    core_auth_expired = False

    for item in sanitized_items:
        name_str = item["name"]
        val_str = item["value"]
        domain_str = item["domain"]
        path_str = item["path"]
        secure_bool = item["secure"]
        http_only_bool = item["httpOnly"]
        same_site_val = item["sameSite"]
        expiry_ts = item["expiry"]

        is_expired = False
        if expiry_ts is not None:
            timestamped_count += 1
            if expiry_ts < now:
                is_expired = True
                expired_count += 1

        # Check core auth
        if name_str.lower() in core_auth_names:
            core_auth_present = True
            if is_expired:
                core_auth_expired = True

        # Check domain matching
        if clean_target:
            if domain_str and domain_matches(domain_str, clean_target):
                domain_matched_count += 1
            elif not domain_str:
                domain_matched_count += 1

        cookie_names.append(name_str)
        sanitized_cookies.append({
            "name": name_str,
            "value": val_str,
            "domain": domain_str or (f".{clean_target}" if clean_target else None),
            "path": path_str,
            "secure": secure_bool,
            "httpOnly": http_only_bool,
            "sameSite": same_site_val,
            "expiry": expiry_ts,
            "is_expired": is_expired,
        })

    # Domain mismatch check
    if clean_target and domain_matched_count == 0:
        return CookieValidationResult(
            is_valid=False,
            status=SessionStatus.DOMAIN_MISMATCH,
            reason=f"Tidak ada cookie yang cocok dengan domain tujuan: '{clean_target}'.",
            cookie_count=len(sanitized_cookies),
            cookie_names=cookie_names,
            sanitized_cookies=sanitized_cookies,
            detected_email=detected_email,
            normalized_json=json.dumps(sanitized_cookies),
        )

    # Expiry check
    if (timestamped_count > 0 and expired_count == timestamped_count) or (core_auth_present and core_auth_expired):
        return CookieValidationResult(
            is_valid=False,
            status=SessionStatus.EXPIRED,
            reason=f"Cookie sesi telah kedaluwarsa ({expired_count}/{timestamped_count} bertanggal kadaluwarsa di masa lalu).",
            cookie_count=len(sanitized_cookies),
            cookie_names=cookie_names,
            sanitized_cookies=sanitized_cookies,
            detected_email=detected_email,
            normalized_json=json.dumps(sanitized_cookies),
        )

    return CookieValidationResult(
        is_valid=True,
        status=SessionStatus.ACTIVE,
        reason=f"Struktur cookie valid ({len(sanitized_cookies)} cookie siap dimuat).",
        cookie_count=len(sanitized_cookies),
        cookie_names=cookie_names,
        sanitized_cookies=sanitized_cookies,
        detected_email=detected_email,
        normalized_json=json.dumps(sanitized_cookies),
    )


def apply_cookies_to_browser(sb: Any, cookies: list[dict], target_url: str) -> tuple[bool, str]:
    """Apply normalized cookies to Chromium via official CDP or WebDriver mechanism.
    
    Pre-navigates to the base domain before applying so the origin security context matches.
    """
    clean_domain = extract_domain(target_url)
    scheme = "https" if "https://" in target_url else "http"
    base_url = f"{scheme}://{clean_domain}/"

    try:
        # Navigate to origin domain first
        sb.get(base_url)
        sb.sleep(1)

        # Clear existing transient cookies safely
        try:
            if hasattr(sb, "clear_cookies"):
                sb.clear_cookies()
        except Exception:
            pass

        # Attempt official SeleniumBase CDP mechanism
        try:
            from mycdp import network as _cdp_net
            cdp_params = []
            for ck in cookies:
                if ck.get("is_expired"):
                    continue

                dom = ck.get("domain") or f".{clean_domain}"
                path = ck.get("path") or "/"
                sec = bool(ck.get("secure", True))
                http_only = bool(ck.get("httpOnly", False))

                ss = None
                ss_val = str(ck.get("sameSite") or "").lower()
                if ss_val == "strict":
                    ss = _cdp_net.CookieSameSite.STRICT
                elif ss_val == "lax":
                    ss = _cdp_net.CookieSameSite.LAX
                elif ss_val in ("none", "no_restriction"):
                    ss = _cdp_net.CookieSameSite.NONE

                expires_ts = None
                if ck.get("expiry") is not None:
                    try:
                        expires_ts = _cdp_net.TimeSinceEpoch(float(ck["expiry"]))
                    except Exception:
                        pass

                param = _cdp_net.CookieParam(
                    name=ck["name"],
                    value=ck["value"],
                    domain=dom,
                    path=path,
                    secure=sec,
                    http_only=http_only,
                    same_site=ss,
                    expires=expires_ts,
                )
                cdp_params.append(param)

            driver = getattr(sb, "driver", sb)
            cdp_cookies = []
            for ck in cookies:
                if ck.get("is_expired"):
                    continue
                item = {
                    "name": ck["name"],
                    "value": ck["value"],
                    "domain": ck.get("domain") or f".{clean_domain}",
                    "path": ck.get("path") or "/",
                    "secure": bool(ck.get("secure", True)),
                    "httpOnly": bool(ck.get("httpOnly", False)),
                }
                if ck.get("sameSite") in ["Strict", "Lax", "None"]:
                    item["sameSite"] = ck["sameSite"]
                if ck.get("expiry"):
                    item["expires"] = float(ck["expiry"])
                cdp_cookies.append(item)

            if hasattr(driver, "execute_cdp_cmd"):
                driver.execute_cdp_cmd("Network.enable", {})
                driver.execute_cdp_cmd("Network.setCookies", {"cookies": cdp_cookies})
                log.info("Successfully applied %d cookies via CDP Network.setCookies", len(cdp_cookies))
            elif hasattr(sb, "set_all_cookies"):
                sb.set_all_cookies(cdp_params)
            else:
                raise AttributeError("CDP setCookies not available")
        except Exception as cdp_err:
            log.debug("CDP cookie injection fallback to webdriver: %s", cdp_err)
            # Fallback to standard WebDriver add_cookie
            driver = getattr(sb, "driver", sb)
            for ck in cookies:
                if ck.get("is_expired"):
                    continue
                cookie_dict: dict[str, Any] = {
                    "name": ck["name"],
                    "value": ck["value"],
                    "path": ck.get("path") or "/",
                }
                if ck.get("domain"):
                    cookie_dict["domain"] = ck["domain"]
                if ck.get("secure") is not None:
                    cookie_dict["secure"] = bool(ck["secure"])
                if ck.get("expiry"):
                    cookie_dict["expiry"] = int(float(ck["expiry"]))
                try:
                    driver.add_cookie(cookie_dict)
                except Exception:
                    pass

        sb.sleep(1)
        sb.get(target_url)
        sb.sleep(2)
        return True, f"Cookie berhasil dimuat ke sesi Chromium untuk domain {clean_domain}."
    except Exception as exc:
        return False, f"Gagal menerapkan cookie ke browser: {str(exc)[:180]}"


def verify_browser_session(
    sb: Any,
    target_url: str,
    account_identifier: str | None = None,
) -> tuple[SessionStatus, str]:
    """Inspect current browser state to verify whether the session is authenticated.
    
    Never attempts automated credential login, CAPTCHA bypass, or MFA circumvention.
    """
    try:
        cur_url = str(sb.get_current_url() or "")
    except Exception:
        cur_url = target_url

    clean_host = extract_domain(cur_url)

    # 1. Target: Google Accounts / Maps / Services
    if "google.com" in clean_host or "google.co.id" in clean_host:
        if "accounts.google.com/signin" in cur_url or "accounts.google.com/v3/signin" in cur_url:
            return SessionStatus.NEEDS_LOGIN, "Sesi Google tidak aktif (dialihkan ke halaman login)."
        if "google.com/account/about" in cur_url:
            return SessionStatus.EXPIRED, "Sesi Google telah kedaluwarsa atau belum terautentikasi."

        # Check for active Google Account profile avatar/button on Maps or Google pages
        try:
            account_elems = sb.find_elements("a[aria-label*='Google Account'], button[aria-label*='Google Account'], a[href*='SignOutOptions']")
            if account_elems:
                for elem in account_elems:
                    label = elem.get_attribute("aria-label") or ""
                    if account_identifier and account_identifier.casefold() in label.casefold():
                        return SessionStatus.ACTIVE, f"Sesi Google aktif dan akun terverifikasi ({account_identifier})."
                return SessionStatus.ACTIVE, "Sesi Google aktif (avatar akun terdeteksi)."
        except Exception:
            pass

        # Check for unauthenticated Sign in button on Google Maps / Search
        try:
            signin_elems = sb.find_elements("a[aria-label*='Sign in'], a[aria-label*='Masuk'], a[href*='accounts.google.com/ServiceLogin']")
            if signin_elems:
                return SessionStatus.NEEDS_LOGIN, "Sesi Google tidak aktif (tombol Sign in muncul)."
        except Exception:
            pass

        if "myaccount.google.com" in cur_url or "/u/" in cur_url or "maps" in cur_url:
            if account_identifier and "@" in account_identifier:
                try:
                    body_text = sb.get_text("body") or ""
                except Exception:
                    body_text = ""
                if account_identifier.casefold() in body_text.casefold():
                    return SessionStatus.ACTIVE, f"Sesi Google aktif dan akun terverifikasi ({account_identifier})."
            return SessionStatus.ACTIVE, "Sesi Google aktif."

    # 2. Target: AutoBotix (https://autobotix.my.id/)
    if "autobotix" in clean_host:
        if "/login" in cur_url:
            return SessionStatus.NEEDS_LOGIN, "Sesi AutoBotix memerlukan login (dialihkan ke /login)."
        try:
            # Check if password login form is present
            has_login_form = sb.is_element_visible("input[type='password']")
            if has_login_form:
                return SessionStatus.NEEDS_LOGIN, "Halaman AutoBotix menampilkan form login."
        except Exception:
            pass
        return SessionStatus.ACTIVE, "Sesi AutoBotix aktif dan terverifikasi."

    # 3. Generic Target Domain
    lower_url = cur_url.lower()
    if any(p in lower_url for p in ("/login", "/signin", "/auth/login", "action=login")):
        return SessionStatus.NEEDS_LOGIN, "Dialihkan ke endpoint login domain target."

    try:
        if sb.is_element_visible("input[type='password']"):
            return SessionStatus.NEEDS_LOGIN, "Halaman tujuan meminta input kata sandi."
    except Exception:
        pass

    return SessionStatus.ACTIVE, f"Sesi aktif pada URL {cur_url[:60]}."


def sync_browser_cookies_to_db(sb: Any, email: str) -> bool:
    """Capture updated/rotated cookies from Chromium and persist back to database.
    
    Ensures rotating tokens (__Secure-1PSIDTS, __Secure-3PSIDTS) are refreshed
    and saved so Google sessions never expire due to token staleness.
    """
    try:
        if not sb or not email:
            return False
        cookies = sb.get_all_cookies() if hasattr(sb, "get_all_cookies") else None
        if not cookies:
            return False
        # Verify essential Google auth tokens exist
        has_auth = any(c.get("name") in ("SID", "__Secure-1PSID", "SAPISID", "SSID") for c in cookies if isinstance(c, dict))
        if not has_auth:
            return False
        val = validate_cookie_payload(cookies, target_domain="google.com")
        if val.is_valid and val.normalized_json:
            db.save_cookie(email, val.normalized_json)
            log.info("Successfully synced %d refreshed Google cookies to database for %s", val.cookie_count, email)
            return True
    except Exception as exc:
        log.debug("Failed to sync browser cookies to DB for %s: %s", email, exc)
    return False


def close_browser_session(sb: Any) -> None:
    """Gracefully close Chromium so in-memory cookies and storage are flushed to persistent profile disk."""
    if sb is None:
        return
    try:
        driver = getattr(sb, "driver", None)
        if driver and hasattr(sb, "loop") and hasattr(driver, "connection"):
            import mycdp
            sb.loop.run_until_complete(driver.connection.send(mycdp.browser.close()))
            time.sleep(0.3)
    except Exception:
        pass
    try:
        if hasattr(sb, "driver") and hasattr(sb.driver, "stop"):
            sb.driver.stop()
        elif hasattr(sb, "quit"):
            sb.quit()
    except Exception:
        pass


class SessionManager:
    """High-level cookie-based session manager."""

    def __init__(self, base_profile_dir: str | Path = "chrome_profiles"):
        self.base_profile_dir = Path(base_profile_dir).resolve()
        db.init_db()
        db.migrate_add_cookie_session_columns()

    def get_profile_path(self, account_email: str) -> Path:
        return get_profile_dir(account_email, base_dir=self.base_profile_dir)

    def acquire_profile_lock(self, account_email: str) -> ProfileLock:
        profile_path = self.get_profile_path(account_email)
        lock = ProfileLock(profile_path)
        lock.acquire()
        return lock

    def load_stored_cookie(self, account_email: str) -> str | None:
        """Fetch raw cookie string from database without modifying it."""
        return db.get_cookie_for_email(account_email)

    def validate_account_cookie(
        self,
        account_email: str,
        target_domain: str | None = "google.com",
    ) -> CookieValidationResult:
        """Validate stored cookie for an account and update status non-destructively."""
        raw_cookie = self.load_stored_cookie(account_email)
        if not raw_cookie:
            res = CookieValidationResult(
                is_valid=False,
                status=SessionStatus.MISSING_COOKIE,
                reason=f"Tidak ada cookie tersimpan untuk akun {account_email}.",
                cookie_count=0,
            )
            db.update_cookie_session_status(account_email, res.status.value, res.reason)
            return res

        res = validate_cookie_payload(raw_cookie, target_domain=target_domain)
        # Update session status in DB non-destructively (never deletes old cookie!)
        db.update_cookie_session_status(account_email, res.status.value, res.reason)
        return res

    def restore_session(
        self,
        sb: Any,
        account_email: str,
        target_url: str = "https://www.google.com/maps?hl=en",
        target_domain: str | None = "google.com",
    ) -> tuple[bool, SessionStatus, str]:
        """Restore cookie session in Chromium without fallback to credentials.
        
        Alur:
        1. Pilih akun & muat cookie tersimpan
        2. Validasi struktur cookie
        3. Terapkan cookie ke Chromium pada domain yang sesuai
        4. Verifikasi status autentikasi di halaman tujuan
        5. Laporkan status (jangan fallback ke email/password/totp jika gagal)
        """
        clean_target = target_domain or extract_domain(target_url)

        # 1 & 2: Muat dan validasi cookie tersimpan
        validation = self.validate_account_cookie(account_email, target_domain=clean_target)
        if not validation.is_valid:
            log.warning(
                "Cookie validation failed for %s (status=%s, reason=%s)",
                account_email, validation.status.value, validation.reason,
            )
            return False, validation.status, validation.reason

        # 3: Terapkan cookie ke browser
        applied, apply_msg = apply_cookies_to_browser(sb, validation.sanitized_cookies, target_url)
        if not applied:
            db.update_cookie_session_status(account_email, SessionStatus.INVALID.value, apply_msg)
            return False, SessionStatus.INVALID, apply_msg

        # 4 & 5: Verifikasi sesi di halaman tujuan
        session_status, detail = verify_browser_session(sb, target_url, account_identifier=account_email)
        db.update_cookie_session_status(account_email, session_status.value, detail)

        if session_status != SessionStatus.ACTIVE:
            log.warning(
                "Session verification failed for %s: status=%s, detail=%s",
                account_email, session_status.value, detail,
            )
            return False, session_status, detail

        log.info("Session verified successfully for %s on %s", account_email, clean_target)
        return True, SessionStatus.ACTIVE, detail


def check_google_account_live(cookie_json_or_list: Any, fallback_email: str = "") -> dict:
    """Inspect cookie live against Google to verify session and retrieve real Account Name.
    Returns:
        {
            "status": "active" | "needs_login" | "invalid",
            "is_valid": bool,
            "account_name": str,
            "email": str,
            "reason": str
        }
    """
    import ssl
    import urllib.error
    import urllib.request

    val = validate_cookie_payload(cookie_json_or_list)
    email = val.detected_email or fallback_email
    if not val.is_valid and val.status == SessionStatus.INVALID:
        return {
            "status": SessionStatus.INVALID.value,
            "is_valid": False,
            "account_name": "",
            "email": email,
            "reason": val.reason,
        }

    # Extract valid cookie tokens
    cookie_parts = []
    has_sid = False
    for ck in val.sanitized_cookies:
        name = ck.get("name") or ""
        value = ck.get("value") or ""
        if name in ("SID", "__Secure-1PSID", "SAPISID", "SSID", "HSID"):
            has_sid = True
        if name and value:
            cookie_parts.append(f"{name}={value}")

    if not has_sid or not cookie_parts:
        return {
            "status": SessionStatus.NEEDS_LOGIN.value,
            "is_valid": False,
            "account_name": "",
            "email": email,
            "reason": "Token sesi login Google (SID / SAPISID) tidak ditemukan dalam cookie.",
        }

    cookie_header = "; ".join(cookie_parts)

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    opener = urllib.request.build_opener(NoRedirect)
    target_url = "https://myaccount.google.com/?hl=id"
    req = urllib.request.Request(
        target_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Cookie": cookie_header,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )

    try:
        resp = opener.open(req, timeout=9)
        final_url = resp.geturl()
        html = resp.read().decode("utf-8", errors="ignore")

        if "accounts.google.com" in final_url or "signin" in final_url or "/intro" in final_url:
            return {
                "status": SessionStatus.NEEDS_LOGIN.value,
                "is_valid": False,
                "account_name": "",
                "email": email,
                "reason": "Sesi Google telah kedaluwarsa atau perlu login ulang.",
            }

        # Session is ACTIVE! Extract Google Account Name
        account_name = ""
        m1 = re.search(r'aria-label="(?:Akun Google|Google Account):\s*([^"\n\r\(]+)', html)
        if m1:
            account_name = m1.group(1).strip()
        else:
            m2 = re.search(r'data-name="([^"]+)"', html)
            if m2:
                account_name = m2.group(1).strip()
            else:
                m3 = re.search(r'\[\s*"([A-Z][a-zA-Z0-9\s]{2,40})"\s*,\s*"[^"]+@gmail\.com"', html)
                if m3:
                    account_name = m3.group(1).strip()

        if not account_name and email:
            uname = email.split("@")[0]
            clean_uname = re.sub(r'[\._0-9]+', ' ', uname).strip()
            if clean_uname:
                account_name = clean_uname.title()

        # Check for refreshed Set-Cookie headers from Google to keep rotating tokens alive
        set_cookies = resp.headers.get_all("Set-Cookie") or []
        if set_cookies and email:
            try:
                from http.cookies import SimpleCookie
                target_keys = {
                    "SID", "HSID", "SSID", "APISID", "SAPISID",
                    "__Secure-1PSID", "__Secure-3PSID",
                    "__Secure-1PSIDTS", "__Secure-3PSIDTS",
                    "LOGIN_INFO", "NID", "AEC"
                }
                raw_existing = db.get_cookie_by_email(email)
                if raw_existing:
                    existing_list = json.loads(raw_existing) if isinstance(raw_existing, str) else list(raw_existing)
                    cookie_map = {c.get("name"): c for c in existing_list if isinstance(c, dict) and c.get("name")}
                    updated_names = []
                    for sc_str in set_cookies:
                        sc = SimpleCookie()
                        try:
                            sc.load(sc_str)
                            for k, morsel in sc.items():
                                if k in target_keys and morsel.value:
                                    if k in cookie_map:
                                        if cookie_map[k].get("value") != morsel.value:
                                            cookie_map[k]["value"] = morsel.value
                                            cookie_map[k]["expirationDate"] = time.time() + (730 * 86400)
                                            updated_names.append(k)
                                    else:
                                        cookie_map[k] = {
                                            "name": k,
                                            "value": morsel.value,
                                            "domain": ".google.com",
                                            "path": "/",
                                            "expirationDate": time.time() + (730 * 86400),
                                            "secure": True,
                                            "httpOnly": True,
                                        }
                                        updated_names.append(k)
                        except Exception:
                            pass

                    if updated_names:
                        merged = list(cookie_map.values())
                        with db.get_db() as conn:
                            conn.execute(
                                "UPDATE cookies SET cookie_json = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
                                (json.dumps(merged), email)
                            )
                        log.info("Refreshed rotating tokens %s for %s via Google HTTP response.", updated_names, email)
            except Exception as e:
                log.debug("Could not auto-merge Set-Cookie for %s: %s", email, e)

        return {
            "status": SessionStatus.ACTIVE.value,
            "is_valid": True,
            "account_name": account_name,
            "email": email,
            "reason": "Sesi cookie Google aktif dan terverifikasi.",
        }

    except urllib.error.HTTPError as err:
        loc = err.headers.get("Location") or ""
        if "accounts.google.com" in loc or "signin" in loc or "intro" in loc or err.code in (301, 302, 303, 307):
            return {
                "status": SessionStatus.NEEDS_LOGIN.value,
                "is_valid": False,
                "account_name": "",
                "email": email,
                "reason": "Sesi Google dialihkan ke login (Perlu Login).",
            }
        return {
            "status": SessionStatus.INVALID.value,
            "is_valid": False,
            "account_name": "",
            "email": email,
            "reason": f"HTTP {err.code}: {err.reason}",
        }
    except Exception as exc:
        return {
            "status": SessionStatus.INVALID.value,
            "is_valid": False,
            "account_name": "",
            "email": email,
            "reason": f"Gagal verifikasi sesi Google: {exc}",
        }
