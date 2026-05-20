from __future__ import annotations

import unittest

from benchmarks.memory_guard import wait_for_memory_budget


class MemoryGuardTests(unittest.TestCase):
    def test_returns_immediately_when_memory_is_ok(self) -> None:
        sleeps: list[float] = []
        logs: list[str] = []

        result = wait_for_memory_budget(
            512,
            15,
            memory_probe=lambda: 1024.0,
            sleep_fn=sleeps.append,
            logger=logs.append,
        )

        self.assertEqual(result, 1024.0)
        self.assertEqual(sleeps, [])
        self.assertEqual(logs, [])

    def test_waits_until_memory_recovers(self) -> None:
        sleeps: list[float] = []
        logs: list[str] = []
        samples = iter([128.0, 256.0, 768.0])

        result = wait_for_memory_budget(
            512,
            20,
            memory_probe=lambda: next(samples),
            sleep_fn=sleeps.append,
            logger=logs.append,
        )

        self.assertEqual(result, 768.0)
        self.assertEqual(sleeps, [20, 20])
        self.assertEqual(len(logs), 2)
        self.assertIn("threshold=512MB", logs[0])


if __name__ == "__main__":
    unittest.main()
