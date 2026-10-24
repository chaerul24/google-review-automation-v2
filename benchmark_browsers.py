"""Local, non-public benchmark for Playwright Chromium and Firefox."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass

import psutil
from playwright.async_api import async_playwright


URL = "data:text/html,<title>automation-benchmark</title><main>dummy</main>"


@dataclass
class Result:
    browser: str
    task: int
    ok: bool
    seconds: float
    rss_mb: float
    error: str = ""


def browser_rss_mb() -> float:
    me = psutil.Process()
    procs = [me] + me.children(recursive=True)
    total = 0
    for proc in procs:
        try:
            if proc.is_running() and proc.name().lower() in {"chromium", "firefox", "firefox-esr"}:
                total += proc.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return total / (1024 * 1024)


async def run_one(kind, executable, task_id: int) -> Result:
    started = time.perf_counter()
    peak = 0.0
    try:
        async with async_playwright() as p:
            launcher = getattr(p, kind)
            kwargs = {"headless": True}
            if executable:
                kwargs["executable_path"] = executable
            if kind == "chromium":
                kwargs["args"] = ["--no-sandbox", "--disable-dev-shm-usage"]
            browser = await launcher.launch(**kwargs)
            peak = max(peak, browser_rss_mb())
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(URL, wait_until="load")
            await page.locator("main").wait_for(state="visible")
            peak = max(peak, browser_rss_mb())
            await browser.close()
        return Result(kind, task_id, True, time.perf_counter() - started, peak)
    except Exception as exc:
        return Result(kind, task_id, False, time.perf_counter() - started, peak, str(exc)[:160])


async def main() -> None:
    os.environ.setdefault("DISPLAY", ":99")
    cases = [("chromium", "/usr/bin/chromium"), ("firefox", "/usr/bin/firefox")]
    for kind, executable in cases:
        results = await asyncio.gather(*(run_one(kind, executable, i) for i in range(1, 4)))
        print(f"{kind}: tasks={len(results)} ok={sum(r.ok for r in results)}")
        for result in results:
            suffix = f" error={result.error}" if result.error else ""
            print(f"  task={result.task} ok={result.ok} seconds={result.seconds:.3f} peak_rss_mb={result.rss_mb:.1f}{suffix}")
        print(f"  wall_clock_parallel={max(r.seconds for r in results):.3f}")

    failed = await run_one("firefox", "/definitely/missing/firefox", 99)
    print(f"failure_case: ok={failed.ok} seconds={failed.seconds:.3f} error={failed.error}")


if __name__ == "__main__":
    asyncio.run(main())
