import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

VIEWPORTS = [
    {"name": "1920x1080_desktop_besar", "width": 1920, "height": 1080, "desc": "Desktop Besar (1920×1080)", "expect_cols": 2},
    {"name": "1440x900_desktop", "width": 1440, "height": 900, "desc": "Desktop (1440×900)", "expect_cols": 2},
    {"name": "1366x768_laptop", "width": 1366, "height": 768, "desc": "Laptop (1366×768)", "expect_cols": 2},
    {"name": "1024x768_laptop_kecil", "width": 1024, "height": 768, "desc": "Laptop Kecil / Tablet Landscape (1024×768)", "expect_cols": 2},
    {"name": "768x1024_tablet_portrait", "width": 768, "height": 1024, "desc": "Tablet Portrait (768×1024)", "expect_cols": 1},
    {"name": "390x844_mobile", "width": 390, "height": 844, "desc": "Mobile Standard (390×844)", "expect_cols": 1},
    {"name": "360x800_mobile_kecil", "width": 360, "height": 800, "desc": "Mobile Kecil (360×800)", "expect_cols": 1},
]

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/chromium"

driver = webdriver.Chrome(options=options)
results = []

try:
    # 1. Login once
    driver.set_window_size(1280, 800)
    driver.get("http://127.0.0.1:5000/login")
    pw = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
    )
    pw.send_keys("wanatawang")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    print("Authentication successful. URL:", driver.current_url)

    for vp in VIEWPORTS:
        print(f"\n=======================================================")
        print(f"Testing {vp['desc']}...")
        driver.set_window_size(vp["width"], vp["height"])
        time.sleep(0.8)

        # 1. Check layout & scroll metrics
        metrics = driver.execute_script("""
            var winW = window.innerWidth;
            var winH = window.innerHeight;
            var docW = document.documentElement.scrollWidth;
            var docH = document.documentElement.scrollHeight;
            
            // Check offending overflow elements
            var offenders = [];
            document.querySelectorAll("*").forEach(function(el) {
                var r = el.getBoundingClientRect();
                if (r.right > winW + 1) {
                    offenders.push(el.tagName + "." + (el.className || ""));
                }
            });

            var panels = document.querySelectorAll('main > section');
            var p1 = panels[0] ? panels[0].getBoundingClientRect() : null;
            var p2 = panels[1] ? panels[1].getBoundingClientRect() : null;

            var videoContainer = document.querySelector('.aspect-video');
            var vRect = videoContainer ? videoContainer.getBoundingClientRect() : null;

            return {
                winW: winW,
                winH: winH,
                docW: docW,
                docH: docH,
                hasHScroll: docW > winW,
                offendersCount: offenders.length,
                p1: p1 ? {x: p1.x, y: p1.y, width: p1.width, height: p1.height} : null,
                p2: p2 ? {x: p2.x, y: p2.y, width: p2.width, height: p2.height} : null,
                video: vRect ? {width: vRect.width, height: vRect.height, ratio: (vRect.width / vRect.height).toFixed(2)} : null
            };
        """)

        # Actual columns detection
        p1 = metrics.get("p1")
        p2 = metrics.get("p2")
        actual_cols = 1
        if p1 and p2:
            if p2["x"] >= (p1["x"] + p1["width"] * 0.75):
                actual_cols = 2
            else:
                actual_cols = 1

        # Check main window vertical scroll on desktop
        desktop_page_scroll_ok = True
        if vp["expect_cols"] == 2:
            desktop_page_scroll_ok = (metrics["docH"] <= metrics["winH"] + 2)

        # Check mobile vertical scrollability
        mobile_scroll_ok = True
        if vp["expect_cols"] == 1:
            mobile_scroll_ok = (metrics["docH"] >= metrics["winH"])

        # 2. Test interactive Tab Switching
        tab_switch_ok = False
        try:
            term_tab = driver.find_element(By.XPATH, "//button[contains(., 'Logcat')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", term_tab)
            time.sleep(0.2)
            term_tab.click()
            time.sleep(0.3)
            
            cfg_tab = driver.find_element(By.XPATH, "//button[contains(., 'Konfigurasi & Kontrol')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cfg_tab)
            time.sleep(0.2)
            cfg_tab.click()
            time.sleep(0.2)
            tab_switch_ok = True
        except Exception as e:
            print("Tab switch exception:", e)

        # 3. Test Cookie Modal dialog fit & responsiveness
        cookie_modal_ok = False
        try:
            cookie_btn = driver.find_element(By.XPATH, "//header//button[contains(@title, 'Cookie')]")
            driver.execute_script("arguments[0].click();", cookie_btn)
            time.sleep(0.4)
            
            # Check modal fits in viewport
            modal_fits = driver.execute_script("""
                var modal = document.querySelector('.fixed.inset-0 .bg-white');
                if (!modal) return false;
                var r = modal.getBoundingClientRect();
                return (r.width <= window.innerWidth && r.height <= window.innerHeight);
            """)
            cookie_modal_ok = bool(modal_fits)
            
            # Close modal
            close_btn = driver.find_element(By.XPATH, "//button[contains(., 'Tutup')]")
            close_btn.click()
            time.sleep(0.3)
        except Exception as e:
            print("Cookie modal exception:", e)

        # 4. Check console errors
        logs = driver.get_log("browser")
        severe_errors = [l for l in logs if l.get("level") == "SEVERE" and "favicon" not in l.get("message", "")]

        # 5. Capture screenshot
        screenshot_path = f"/root/.gemini/antigravity-cli/brain/a8747ff4-b544-4f58-a5a2-1ed1aac6b6d6/{vp['name']}.png"
        driver.save_screenshot(screenshot_path)

        res = {
            "name": vp["name"],
            "desc": vp["desc"],
            "viewport": f"{vp['width']}x{vp['height']}",
            "expected_cols": vp["expect_cols"],
            "actual_cols": actual_cols,
            "horizontal_overflow": metrics["hasHScroll"],
            "doc_width": metrics["docW"],
            "doc_height": metrics["docH"],
            "video_aspect_ratio": metrics["video"]["ratio"] if metrics.get("video") else None,
            "desktop_constrained": desktop_page_scroll_ok,
            "mobile_scrollable": mobile_scroll_ok,
            "tab_switch_working": tab_switch_ok,
            "modal_responsive_ok": cookie_modal_ok,
            "severe_console_errors": len(severe_errors),
            "screenshot": screenshot_path
        }
        results.append(res)
        print(f"  Layout: {actual_cols} Kolom (Ekspektasi: {vp['expect_cols']} Kolom)")
        print(f"  Horizontal Overflow: {'ADA (FAIL)' if metrics['hasHScroll'] else 'TIDAK ADA (PASS)'} (docW={metrics['docW']}, winW={metrics['winW']})")
        print(f"  Video Ratio: {res['video_aspect_ratio']} (16:9 target ~1.78)")
        print(f"  Tabs Switching: {'OK' if tab_switch_ok else 'FAIL'}")
        print(f"  Modal Fit: {'OK' if cookie_modal_ok else 'FAIL'}")
        print(f"  Severe Errors: {len(severe_errors)}")
        print(f"  Screenshot: {screenshot_path}")

    # Summary table
    print("\n\n=======================================================")
    print("FINAL RESPONSIVE TEST SUITE REPORT:")
    print("=======================================================")
    print(json.dumps(results, indent=2))

finally:
    driver.quit()
