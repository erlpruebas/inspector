from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from typing import Callable


def free_memory_mb() -> float | None:
    if os.name == "nt":
        return _free_memory_mb_windows()
    return _free_memory_mb_posix()


def wait_for_memory_budget(
    min_free_memory_mb: int,
    poll_seconds: int,
    *,
    memory_probe: Callable[[], float | None] = free_memory_mb,
    sleep_fn: Callable[[float], None] = time.sleep,
    logger: Callable[[str], None] = print,
) -> float | None:
    if min_free_memory_mb <= 0:
        return None

    sleep_interval = max(1, poll_seconds)
    while True:
        free_mb = memory_probe()
        if free_mb is None:
            return None
        if free_mb >= min_free_memory_mb:
            return free_mb

        logger(
            f"[memory-wait] free={free_mb:.0f}MB threshold={min_free_memory_mb}MB "
            f"sleeping={sleep_interval}s"
        )
        sleep_fn(sleep_interval)


def _free_memory_mb_windows() -> float | None:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):  # type: ignore[attr-defined]
        return None
    return float(status.ullAvailPhys) / (1024 * 1024)


def _free_memory_mb_posix() -> float | None:
    try:
        avail_pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError):
        return None
    if avail_pages <= 0 or page_size <= 0:
        return None
    return float(avail_pages * page_size) / (1024 * 1024)
