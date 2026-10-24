import asyncio
import os
import tempfile
import time
import unittest

from dry_run_workers import DryRunChromiumPool


class DryRunPoolTests(unittest.TestCase):
    def test_concurrency_limit_and_cleanup(self):
        async def scenario():
            events = []

            async def report(status):
                events.append((status.worker_id, status.state, time.monotonic()))

            pool = DryRunChromiumPool(max_workers=2, duration=0.4, inter_task_delay=0, on_status=report)
            try:
                results = await pool.run(["about:blank"] * 4)
                self.assertEqual(len(results), 4)
                self.assertTrue(all(r.state == "Completed" for r in results))
                starts = [t for _, state, t in events if state == "Running"]
                finishes = [t for _, state, t in events if state == "Completed"]
                self.assertEqual(len(starts), 4)
                self.assertEqual(len(finishes), 4)
                self.assertGreaterEqual(min(finishes) - min(starts), 0.3)
                self.assertEqual(pool._processes, {})
            finally:
                await pool.stop()
                pool.close()

        asyncio.run(scenario())

    def test_stop_marks_workers_without_orphans(self):
        async def scenario():
            pool = DryRunChromiumPool(max_workers=3, duration=30, inter_task_delay=0)
            task = asyncio.create_task(pool.run(["about:blank"] * 3))
            await asyncio.sleep(0.5)
            await pool.stop()
            results = await task
            self.assertTrue(all(r.state in {"Stopped", "Completed"} for r in results))
            self.assertEqual(pool._processes, {})
            pool.close()

        asyncio.run(scenario())

    def test_worker_failure_isolated(self):
        async def scenario():
            events = []
            with tempfile.NamedTemporaryFile("w", delete=False) as script:
                script.write(
                    "#!/usr/bin/env python3\n"
                    "import sys, time\n"
                    "if sys.argv[-1].startswith('fail://'): sys.exit(7)\n"
                    "time.sleep(0.05)\n"
                )
                executable = script.name
            os.chmod(executable, 0o755)

            async def report(status):
                events.append(status)

            pool = DryRunChromiumPool(
                max_workers=2,
                duration=0.5,
                inter_task_delay=0,
                chromium=executable,
                on_status=report,
            )
            try:
                results = await pool.run(["fail://worker-1", "about:blank"])
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0].state, "Failed")
                self.assertEqual(results[1].state, "Completed")
                self.assertTrue(results[0].error)
                self.assertEqual(pool._processes, {})
            finally:
                await pool.stop()
                pool.close()
                os.unlink(executable)

        asyncio.run(scenario())

    def test_dry_run_delay_is_exact_and_explicit(self):
        async def scenario():
            events = []

            async def report(status):
                events.append((status.worker_id, status.state, status.message, time.monotonic()))

            pool = DryRunChromiumPool(max_workers=1, duration=0.1, inter_task_delay=0.2, on_status=report)
            try:
                results = await pool.run(["about:blank", "about:blank"])
                self.assertTrue(all(r.state == "Completed" for r in results))
                waits = [e for e in events if e[2] and "Menunggu 0.2 detik" in e[2]]
                self.assertEqual(len(waits), 1)
                starts = [t for _, state, _, t in events if state == "Running"]
                self.assertGreaterEqual(starts[1] - starts[0], 0.18)
            finally:
                await pool.stop()
                pool.close()

        asyncio.run(scenario())

    def test_three_tasks_overlap_and_next_wave_waits(self):
        async def scenario():
            events = []

            async def report(status):
                events.append(status)

            pool = DryRunChromiumPool(max_workers=2, duration=0.25, inter_task_delay=0.2, on_status=report)
            try:
                results = await pool.run(["about:blank"] * 3)
                self.assertTrue(all(r.state == "Completed" for r in results))
                starts = {s.worker_id: s.started_at for s in results}
                finishes = {s.worker_id: s.finished_at for s in results}
                self.assertLess(abs(starts[1] - starts[2]), 0.15)
                self.assertGreaterEqual(starts[3] - min(finishes[1], finishes[2]), 0.18)
                self.assertEqual(pool._processes, {})
            finally:
                await pool.stop()
                pool.close()

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
