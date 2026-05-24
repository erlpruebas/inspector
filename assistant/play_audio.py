import argparse
import ctypes
import time
from pathlib import Path


winmm = ctypes.windll.winmm


def mci(command: str) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    result = winmm.mciSendStringW(command, buffer, len(buffer), 0)
    if result:
        err = ctypes.create_unicode_buffer(256)
        winmm.mciGetErrorStringW(result, err, len(err))
        raise RuntimeError(f"{command}: {err.value}")
    return buffer.value


def play(path: Path, timeout: float) -> None:
    alias = f"inspector_alarm_{int(time.time() * 1000)}"
    file_path = str(path.resolve())
    try:
        mci(f'open "{file_path}" type mpegvideo alias {alias}')
        mci(f"play {alias}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            mode = mci(f"status {alias} mode").strip().lower()
            if mode not in {"playing", "seeking"}:
                break
            time.sleep(0.2)
    finally:
        try:
            mci(f"close {alias}")
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    play(Path(args.file), args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
