"""Safe multi-Chromium dry-run pool.

This module intentionally never logs in, clicks a review form, or submits
public content. It only opens URLs in isolated Chromium profiles so browser
concurrency and cleanup can be tested safely.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import shutil
import signal
import tempfile
import time
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable


@dataclass
class WorkerStatus:
    worker_id: int
    state: str = "Starting"
    url: str = ""
    pid: int | None = None
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    message: str | None = None

    @property
    def duration_s(self) -> float | None:
        """Wall-clock duration once the worker has finished."""
        if self.started_at is None:
            return None
        end = self.finished_at or time.time()
        return max(0.0, end - self.started_at)


StatusCallback = Callable[[WorkerStatus], Awaitable[None] | None]


class DryRunChromiumPool:
    """Run isolated Chromium previews concurrently with a hard worker limit."""

    def __init__(
        self,
        max_workers: int = 2,
        duration: float = 5,
        inter_task_delay: float = 0,
        display: str | None = None,
        chromium: str = "chromium",
        on_status: StatusCallback | None = None,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self.max_workers = max_workers
        self.duration = max(0.1, duration)
        if inter_task_delay < 0:
            raise ValueError("inter_task_delay cannot be negative")
        self.inter_task_delay = float(inter_task_delay)
        self.display = display or os.environ.get("DISPLAY", ":99")
        self.chromium = chromium
        self.on_status = on_status
        self._processes: dict[int, asyncio.subprocess.Process] = {}
        self._active = 0
        self._stopping = False
        storage_env = os.environ.get("BROWSER_AUTOMATION_STORAGE")
        if storage_env:
            storage_root = Path(storage_env)
            if not storage_root.is_dir() or not os.access(storage_root, os.W_OK):
                raise RuntimeError(
                    f"BROWSER_AUTOMATION_STORAGE tidak tersedia atau tidak writable: {storage_root}"
                )
            temp_root = storage_root / "temp"
            temp_root.mkdir(parents=True, exist_ok=True)
        else:
            # Local CLI fallback; the service sets the persistent HDD path.
            temp_root = Path("/dev/shm")
        self._profile_root = Path(tempfile.mkdtemp(prefix="review-dry-run-", dir=str(temp_root)))

    async def _emit(self, status: WorkerStatus) -> None:
        if self.on_status:
            result = self.on_status(status)
            if result is not None:
                await result

    async def _run_one(self, worker_id: int, url: str, slot: asyncio.Semaphore) -> WorkerStatus:
        status = WorkerStatus(worker_id=worker_id, url=url)
        await self._emit(status)
        async with slot:
            if self._stopping:
                status.state = "Stopped"
                await self._emit(status)
                return status
            if self.inter_task_delay and worker_id > self.max_workers:
                status.message = (
                    f"[DRY-RUN] Menunggu {self.inter_task_delay:g} detik "
                    "sebelum tugas berikutnya."
                )
                await self._emit(status)
                remaining = self.inter_task_delay
                while remaining > 0:
                    step = min(1.0, remaining)
                    await asyncio.sleep(step)
                    remaining -= step
                    status.message = (
                        f"[DRY-RUN] Countdown tugas berikutnya: "
                        f"{math.ceil(max(0.0, remaining)):g} detik."
                    )
                    await self._emit(status)
                status.message = None
            profile = self._profile_root / f"worker-{worker_id}"
            profile.mkdir()
            try:
                self._active += 1
                process = await asyncio.create_subprocess_exec(
                    self.chromium,
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                    "--no-default-browser-check",
                    f"--user-data-dir={profile}",
                    f"--window-position={(worker_id - 1) * 40},54",
                    "--window-size=960,600",
                    url,
                    env={**os.environ, "DISPLAY": self.display},
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,
                )
                self._processes[worker_id] = process
                status.pid = process.pid
                status.started_at = time.time()
                status.state = "Running"
                await self._emit(status)
                try:
                    await asyncio.wait_for(process.wait(), timeout=self.duration)
                except asyncio.TimeoutError:
                    status.state = "Completed"
                    process.terminate()
                    await process.wait()
                if process.returncode == 0:
                    status.state = "Completed"
                if self._stopping and process.returncode is not None:
                    status.state = "Stopped"
                if process.returncode not in (0, -signal.SIGTERM, 143) and status.state != "Completed":
                    status.state = "Failed"
                    stderr = (await process.stderr.read()).decode(errors="replace").strip()
                    status.error = stderr[-500:] or f"Chromium exited with code {process.returncode}"
            except asyncio.CancelledError:
                status.state = "Stopped"
                raise
            except Exception as exc:  # one worker must not cancel siblings
                status.state = "Failed"
                status.error = str(exc)
            finally:
                self._active = max(0, self._active - 1)
                status.finished_at = time.time()
                self._processes.pop(worker_id, None)
                shutil.rmtree(profile, ignore_errors=True)
                await self._emit(status)
        return status

    async def run(self, urls: list[str]) -> list[WorkerStatus]:
        slot = asyncio.Semaphore(self.max_workers)
        tasks = [asyncio.create_task(self._run_one(i, url, slot)) for i, url in enumerate(urls, 1)]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def stop(self) -> None:
        self._stopping = True
        for process in list(self._processes.values()):
            if process.returncode is None:
                process.terminate()
        await asyncio.gather(*(p.wait() for p in self._processes.values()), return_exceptions=True)

    def close(self) -> None:
        shutil.rmtree(self._profile_root, ignore_errors=True)


async def _main(args: argparse.Namespace) -> None:
    events: list[WorkerStatus] = []
    active: set[int] = set()
    terminal = {"Completed", "Failed", "Stopped"}

    async def report(status: WorkerStatus) -> None:
        events.append(status)
        if status.state == "Running":
            active.add(status.worker_id)
        elif status.state in terminal:
            active.discard(status.worker_id)
        duration = f" duration={status.duration_s:.2f}s" if status.duration_s is not None else ""
        message = f" message={status.message}" if status.message else ""
        if status.state == "Running" and status.started_at:
            print(
                f"[DRY-RUN] Tugas {status.worker_id} mulai "
                f"{datetime.fromtimestamp(status.started_at).astimezone().isoformat(timespec='seconds')}",
                flush=True,
            )
        elif status.state in terminal and status.finished_at:
            print(
                f"[DRY-RUN] Tugas {status.worker_id} selesai "
                f"{datetime.fromtimestamp(status.finished_at).astimezone().isoformat(timespec='seconds')}",
                flush=True,
            )
        print(
            f"worker={status.worker_id} state={status.state} pid={status.pid or '-'}"
            f" active={len(active)}{duration}{message} url={status.url}",
            flush=True,
        )

    pool = DryRunChromiumPool(
        args.workers,
        args.duration,
        inter_task_delay=args.delay,
        on_status=report,
    )
    try:
        await pool.run(args.url)
    finally:
        await pool.stop()
        pool.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safe parallel Chromium dry-run")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--duration", type=float, default=5)
    parser.add_argument("--delay", type=float, default=0,
                        help="optional delay between dry-run task waves (seconds; default: 0)")
    parser.add_argument("url", nargs="+", default=["about:blank"])
    asyncio.run(_main(parser.parse_args()))
