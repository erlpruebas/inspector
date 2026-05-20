from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable

from .detectors import DetectedEntity


@dataclass
class MiniNanoPrivacyReviewer:
    base_url: str
    api_key: str = "local"
    model: str = "gemini-nano-local"
    timeout_seconds: int = 120

    @classmethod
    def from_env(cls) -> "MiniNanoPrivacyReviewer":
        return cls(
            base_url=os.getenv("BENCH_VIKING_NANO_BASE_URL", "http://127.0.0.1:8788/v1/chat/completions"),
            api_key=os.getenv("BENCH_VIKING_NANO_API_KEY", "local"),
            model=os.getenv("BENCH_VIKING_NANO_MODEL", "gemini-nano-local"),
            timeout_seconds=int(os.getenv("BENCH_VIKING_NANO_API_TIMEOUT", "120")),
        )

    def review(self, text: str) -> list[DetectedEntity]:
        chunks = _chunk_text(text)
        findings: list[DetectedEntity] = []
        for index, chunk in enumerate(chunks, start=1):
            prompt = _build_prompt(chunk, index, len(chunks))
            payload = self._call(prompt)
            if not payload:
                continue
            for item in payload:
                if not isinstance(item, dict):
                    continue
                entity_type = str(item.get("entity_type", "")).strip().upper()
                candidate = str(item.get("text", "")).strip()
                if not entity_type or not candidate:
                    continue
                confidence = float(item.get("confidence", 0.0) or 0.0)
                reason = str(item.get("reason", "")).strip()
                if confidence < 0.75:
                    continue
                if candidate not in chunk:
                    continue
                start = chunk.find(candidate)
                findings.append(
                    DetectedEntity(
                        start=start,
                        end=start + len(candidate),
                        text=candidate,
                        entity_type=entity_type,
                        confidence=confidence,
                        source=f"mini_nano:{reason}" if reason else "mini_nano",
                    )
                )
        return findings

    def _call(self, prompt: str) -> list[dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "privacy-guard-mini-nano/1.0",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return only JSON. Do not rewrite the text. Detect possible sensitive entities.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 256,
        }
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
            return []
        text = _extract_content(data)
        return _parse_json_array(text)


def _chunk_text(text: str, chunk_size: int = 2500) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > chunk_size and current:
            chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks or [text]


def _build_prompt(chunk: str, index: int, total: int) -> str:
    return (
        f"Chunk {index}/{total}. Return a JSON array of possible sensitive entities found in the text.\n"
        "Each item must have: text, entity_type, confidence, reason.\n"
        "Allowed types: PERSON, ORG, EMAIL, PHONE, ADDRESS, ID_NUMBER, BANK, DATE, URL, CONTRACT, CASE, OTHER.\n"
        "Only include items that appear verbatim in the chunk.\n\n"
        "Text:\n<<<\n"
        + chunk
        + "\n>>>"
    )


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return json.dumps(data, ensure_ascii=False)
    message = choices[0].get("message") or {}
    return str(message.get("content", "")).strip()


def _parse_json_array(text: str) -> list[dict[str, Any]]:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
    if not candidate.startswith("["):
        start = candidate.find("[")
        end = candidate.rfind("]")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    try:
        raw = json.loads(candidate)
    except json.JSONDecodeError:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []

