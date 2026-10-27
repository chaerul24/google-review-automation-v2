"""Automated VM Browser & Cookie Injection Engine for Proxmox KVM Windows VMs.

Controls Edge inside Windows VM via QMP and Chrome DevTools Protocol (CDP),
automatically injecting stored Google session cookies without manual user interaction.
"""

import argparse
import json
import logging
import os
import socket
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
log = logging.getLogger("vm_bot_runner")

HOST_API_BASE = "http://192.168.1.17:5000"

HMP_MAP = {
    " ": "spc", ".": "dot", "/": "slash", "-": "minus",
    ":": "shift-semicolon", ";": "semicolon", "\\": "backslash",
    "\"": "shift-apostrophe", "'": "apostrophe", "&": "shift-7",
    "=": "equal", "*": "shift-8", "_": "shift-minus"
}
for c in "abcdefghijklmnopqrstuvwxyz0123456789":
    HMP_MAP[c] = c
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    HMP_MAP[c] = f"shift-{c.lower()}"


def get_qmp(vmid: int):
    sock_path = f"/var/run/qemu-server/{vmid}.qmp"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(10.0)
    s.connect(sock_path)
    s.recv(2048)
    s.sendall(b'{"execute": "qmp_capabilities"}\n')
    s.recv(2048)
    return s


def send_hmp(s, key: str):
    cmd = {"execute": "human-monitor-command", "arguments": {"command-line": f"sendkey {key}"}}
    s.sendall((json.dumps(cmd) + "\n").encode())
    return s.recv(2048)


def type_string(s, text: str, delay: float = 0.02):
    for ch in text:
        k = HMP_MAP.get(ch)
        if k:
            send_hmp(s, k)
            time.sleep(delay)


def run_dialog_command(s, command_line: str):
    # 1. Dismiss any stuck window/dialog first
    cmd_alt_f4 = {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": "alt_l"}, {"type": "qcode", "data": "f4"}]}}
    s.sendall((json.dumps(cmd_alt_f4) + "\n").encode())
    s.recv(2048)
    time.sleep(0.3)
    send_hmp(s, "esc")
    time.sleep(0.3)

    # 2. Win+D to ensure clean desktop focus
    cmd_win_d = {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": "meta_l"}, {"type": "qcode", "data": "d"}]}}
    s.sendall((json.dumps(cmd_win_d) + "\n").encode())
    s.recv(2048)
    time.sleep(0.8)

    # 3. Win+R
    cmd_win_r = {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": "meta_l"}, {"type": "qcode", "data": "r"}]}}
    s.sendall((json.dumps(cmd_win_r) + "\n").encode())
    s.recv(2048)
    time.sleep(1.2)

    # 4. Click directly inside the text box to guarantee focus: (x=120, y=610) -> (0.1172, 0.7942)
    x_val = int(0.1172 * 32767)
    y_val = int(0.7942 * 32767)
    cmd_move = {"execute": "input-send-event", "arguments": {"events": [{"type": "abs", "data": {"axis": "x", "value": x_val}}, {"type": "abs", "data": {"axis": "y", "value": y_val}}]}}
    s.sendall((json.dumps(cmd_move) + "\n").encode())
    s.recv(2048)
    time.sleep(0.1)

    cmd_click = {"execute": "input-send-event", "arguments": {"events": [{"type": "btn", "data": {"button": "left", "down": True}}, {"type": "btn", "data": {"button": "left", "down": False}}]}}
    s.sendall((json.dumps(cmd_click) + "\n").encode())
    s.recv(2048)
    time.sleep(0.3)

    # 5. Clear text in Run dialog
    send_hmp(s, "ctrl-a")
    time.sleep(0.2)
    send_hmp(s, "backspace")
    time.sleep(0.2)

    # 6. Type command
    type_string(s, command_line, delay=0.015)
    time.sleep(0.5)

    # 7. Submit via OK button click at (x=160, y=680) and Enter key
    x_ok = int(0.1562 * 32767)
    y_ok = int(0.8854 * 32767)
    cmd_move_ok = {"execute": "input-send-event", "arguments": {"events": [{"type": "abs", "data": {"axis": "x", "value": x_ok}}, {"type": "abs", "data": {"axis": "y", "value": y_ok}}]}}
    s.sendall((json.dumps(cmd_move_ok) + "\n").encode())
    s.recv(2048)
    time.sleep(0.1)

    cmd_click_ok = {"execute": "input-send-event", "arguments": {"events": [{"type": "btn", "data": {"button": "left", "down": True}}, {"type": "btn", "data": {"button": "left", "down": False}}]}}
    s.sendall((json.dumps(cmd_click_ok) + "\n").encode())
    s.recv(2048)
    time.sleep(0.3)

    send_hmp(s, "ret")
    time.sleep(1.0)


def wake_vm_if_asleep(s, vmid: int):
    """Ensure VM display and input are active before launching commands."""
    try:
        move_cmd = {
            "execute": "input-send-event",
            "arguments": {
                "events": [
                    {"type": "rel", "data": {"axis": "x", "value": 5}},
                    {"type": "rel", "data": {"axis": "y", "value": 5}},
                ]
            }
        }
        s.sendall((json.dumps(move_cmd) + "\n").encode())
        s.recv(1024)
        shift_cmd = {
            "execute": "send-key",
            "arguments": {"keys": [{"type": "qcode", "data": "shift_l"}]}
        }
        s.sendall((json.dumps(shift_cmd) + "\n").encode())
        s.recv(1024)
    except Exception as e:
        log.warning(f"Could not send wake event to VM {vmid}: {e}")


def inject_cookies_to_vm(
    vmid: int = 101,
    email_ident: str = "auto",
    target_url: str = "https://www.google.com/maps",
    business_id: int = None,
    review_id: int = None,
    business_name: str = "",
    star_rating: int = 5,
    review_text: str = "",
    timeout_sec: int = 120,
):
    """Automates cookie injection into VM Edge browser via CDP without manual interaction."""
    log.info(f"Injecting cookies into VM {vmid} for account identifier '{email_ident}'...")

    # Write task specification for this VM to disk so the host API serves it
    task_file = f"/tmp/vm_task_{vmid}.json"
    task_spec = {
        "vmid": vmid,
        "email": email_ident,
        "target_url": target_url,
        "business_id": business_id,
        "review_id": review_id,
        "business_name": business_name,
        "star_rating": star_rating,
        "review_text": review_text,
    }
    try:
        with open(task_file, "w") as f:
            json.dump(task_spec, f, indent=2)
    except Exception as e:
        log.warning(f"Failed to write {task_file}: {e}")

    # Clear VM-specific debug log
    vm_log_file = f"/tmp/vm_{vmid}_debug.log"
    try:
        open(vm_log_file, "w").close()
    except Exception:
        pass

    # Step 1: Connect QMP and trigger runner
    s = get_qmp(vmid)
    try:
        wake_vm_if_asleep(s, vmid)

        # Run command via Run dialog: download latest inject.ps1 and run
        runner = f"powershell -c \"curl.exe -s {HOST_API_BASE}/static/inject.ps1 -o c:\\users\\public\\inject.ps1; powershell -ep bypass -file c:\\users\\public\\inject.ps1 -vmid {vmid}\""
        log.info(f"Triggering runner on VM {vmid} via Run dialog...")
        run_dialog_command(s, runner)
    finally:
        # Close QMP socket immediately so it does not block screenshare or other threads
        try:
            s.close()
        except Exception:
            pass

    # Step 2: Wait for injection log from VM
    log.info(f"Waiting for CDP injection confirmation from VM {vmid}...")
    completed = False
    max_attempts = int(timeout_sec / 1.5)
    for i in range(max_attempts):
        time.sleep(1.5)
        try:
            if os.path.exists(vm_log_file):
                with open(vm_log_file, "r") as f:
                    log_text = f.read()
                if "INJECTION COMPLETE SUCCESS" in log_text:
                    log.info(f"Successfully received INJECTION COMPLETE SUCCESS from VM {vmid}!")
                    completed = True
                    break
                elif "FATAL ERROR" in log_text:
                    log.error(f"VM {vmid} reported error: {log_text}")
                    break
        except Exception:
            pass
        if i > 0 and i % 4 == 0:
            log.info(f"Waiting for VM {vmid} injection... ({i*1.5:.0f}s)")

    # Step 3: Take verification screenshot
    try:
        screenshot_path = f"/tmp/vm_{vmid}_injected.png"
        ppm_path = f"/tmp/vm_{vmid}_injected.ppm"
        s2 = get_qmp(vmid)
        try:
            cmd_dump = {"execute": "screendump", "arguments": {"filename": ppm_path}}
            s2.sendall((json.dumps(cmd_dump) + "\n").encode())
            s2.recv(2048)
        finally:
            s2.close()

        from PIL import Image
        im = Image.open(ppm_path)
        im.save(screenshot_path)
        try:
            Path(ppm_path).unlink()
        except OSError:
            pass
        log.info(f"Verification screenshot saved to {screenshot_path}")
    except Exception as e:
        log.warning(f"Could not capture verification screendump: {e}")

    return completed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate cookie injection into Windows VM Edge browser")
    parser.add_argument("--vmid", type=int, default=101, help="Target Proxmox VM ID (e.g. 101)")
    parser.add_argument("--email", default="auto", help="Account email or identifier in database")
    parser.add_argument("--url", default="https://www.google.com/maps", help="Target URL to open")
    args = parser.parse_args()

    ok = inject_cookies_to_vm(args.vmid, args.email, args.url)
    sys.exit(0 if ok else 1)
