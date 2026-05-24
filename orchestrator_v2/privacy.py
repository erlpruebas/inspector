from __future__ import annotations

from pathlib import Path


def copy_input_files(files: tuple[Path, ...], workdir: Path) -> list[Path]:
    import shutil

    copied: list[Path] = []
    for source in files:
        source = source.resolve()
        if not source.exists() or not source.is_file():
            continue
        target = workdir / source.name
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def apply_optional_privacy(workdir: Path, mode: str) -> dict:
    if mode == "clear":
        return {"mode": "clear"}
    try:
        from benchmarks.privacy_guard import DEFAULT_STORE_PATH, apply_privacy_to_workdir
    except ImportError:
        return {"mode": mode, "error": "privacy_guard no disponible"}
    result = apply_privacy_to_workdir(workdir, mode=mode, store_path=DEFAULT_STORE_PATH)
    return result.to_dict()

