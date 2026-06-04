from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_PY_FILE_RE = re.compile(r"(?P<name>[\w .\-]+\.py)\b", re.IGNORECASE)
_REPAIR_HINT_RE = re.compile(
    r"\b(?:corrige|repara|arregla|fix|repair|correct)\b.*\b(?:sintaxis|syntax)\b|"
    r"\b(?:sintaxis|syntax)\b.*\b(?:corrige|repara|arregla|fix|repair|correct)\b",
    re.IGNORECASE | re.DOTALL,
)
_BLOCK_START_RE = re.compile(
    r"^\s*(?:if|elif|else|for|while|try|except|finally|with|def|class|match|case)\b"
)


@dataclass(frozen=True)
class PythonRepairResult:
    path: Path
    message: str


def repair_python_syntax_if_requested(instruction: str, workdir: Path) -> PythonRepairResult | None:
    """Apply safe, mechanical Python syntax fixes before invoking Codex.

    This intentionally handles only narrow syntax-repair requests. It compiles
    the file, applies a small fix for common missing colons, then compiles again.
    It never executes user code.
    """
    if not _looks_like_python_syntax_repair(instruction):
        return None

    path = _target_python_file(instruction, workdir)
    if path is None or not path.exists() or not path.is_file():
        return None

    original = path.read_text(encoding="utf-8", errors="replace")
    try:
        compile(original, str(path), "exec")
        return PythonRepairResult(path=path, message=f"{path.name} ya compila correctamente; no he cambiado el archivo.")
    except SyntaxError as exc:
        fixed = _fix_missing_colon(original, exc)

    if fixed == original:
        return None

    try:
        compile(fixed, str(path), "exec")
    except SyntaxError:
        return None

    path.write_text(fixed, encoding="utf-8")
    return PythonRepairResult(
        path=path,
        message=f"He corregido la sintaxis de {path.name} y el archivo ya compila correctamente.",
    )


def _looks_like_python_syntax_repair(instruction: str) -> bool:
    return bool(_PY_FILE_RE.search(instruction) and _REPAIR_HINT_RE.search(instruction))


def _target_python_file(instruction: str, workdir: Path) -> Path | None:
    matches = [match.group("name").strip() for match in _PY_FILE_RE.finditer(instruction)]
    for name in matches:
        candidate = (workdir / name).resolve()
        try:
            candidate.relative_to(workdir.resolve())
        except ValueError:
            continue
        if candidate.exists():
            return candidate
    py_files = sorted(workdir.glob("*.py"))
    if len(py_files) == 1:
        return py_files[0]
    return None


def _fix_missing_colon(source: str, exc: SyntaxError) -> str:
    if exc.lineno is None or exc.lineno < 1:
        return source

    lines = source.splitlines(keepends=True)
    index = exc.lineno - 1
    if index >= len(lines):
        return source

    line = lines[index]
    newline = ""
    if line.endswith("\r\n"):
        newline = "\r\n"
        body = line[:-2]
    elif line.endswith("\n"):
        newline = "\n"
        body = line[:-1]
    else:
        body = line

    stripped = body.rstrip()
    if stripped.endswith(":") or not _BLOCK_START_RE.match(stripped):
        return source

    lines[index] = f"{stripped}:{newline}"
    return "".join(lines)
