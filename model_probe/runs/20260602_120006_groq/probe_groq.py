import argparse
import base64
import hashlib
import json
import math
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid
import wave
from pathlib import Path


BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
CHAT_MODEL = os.environ.get("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
STT_MODEL = os.environ.get("GROQ_STT_MODEL", "whisper-large-v3-turbo")
TTS_MODEL = os.environ.get("GROQ_TTS_MODEL", "canopylabs/orpheus-v1-english")
TTS_VOICE = os.environ.get("GROQ_TTS_VOICE", "austin")
TIMEOUT_SECONDS = float(os.environ.get("GROQ_TIMEOUT_SECONDS", "60"))


def get_api_key():
    return os.environ.get("GROQ_API_KEY") or os.environ.get("PROVIDER_API_KEY")


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def make_wav(path, seconds=1.0, rate=16000):
    # A tiny tone fixture keeps the STT upload independent of local microphone/TTS.
    amplitude = 6000
    frequency = 440.0
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        for idx in range(frames):
            sample = int(amplitude * math.sin(2 * math.pi * frequency * idx / rate))
            wav.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))


def request_json(method, url, api_key, payload=None):
    headers = {"Authorization": f"Bearer {api_key}"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    return timed_request(req)


def multipart_request(url, api_key, fields, files):
    boundary = f"----groq-probe-{uuid.uuid4().hex}"
    body = bytearray()

    def add_part(name, value, filename=None, content_type=None):
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        if filename:
            body.extend(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(
                    "utf-8"
                )
            )
            body.extend(f"Content-Type: {content_type or 'application/octet-stream'}\r\n\r\n".encode("utf-8"))
            body.extend(value)
            body.extend(b"\r\n")
        else:
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")

    for key, value in fields.items():
        add_part(key, value)
    for key, file_path in files.items():
        file_path = Path(file_path)
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        add_part(key, file_path.read_bytes(), file_path.name, content_type)

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    return timed_request(req)


def timed_request(req):
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            body = resp.read()
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            return {
                "ok": 200 <= resp.status < 300,
                "status": resp.status,
                "elapsed_ms": elapsed_ms,
                "headers": {
                    "content_type": resp.headers.get("Content-Type"),
                    "request_id": resp.headers.get("x-request-id"),
                },
                "body_bytes": len(body),
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "ok": False,
            "status": exc.code,
            "elapsed_ms": elapsed_ms,
            "headers": {
                "content_type": exc.headers.get("Content-Type") if exc.headers else None,
                "request_id": exc.headers.get("x-request-id") if exc.headers else None,
            },
            "body_bytes": len(body),
            "body": body,
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": elapsed_ms,
            "headers": {},
            "body_bytes": 0,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "body": b"",
        }


def decode_body(raw):
    body = raw.pop("body", b"")
    content_type = (raw.get("headers") or {}).get("content_type") or ""
    if not body:
        return raw
    if "json" in content_type:
        try:
            raw["json"] = json.loads(body.decode("utf-8"))
            return raw
        except Exception:
            pass
    if content_type.startswith("audio/") or content_type in {"application/octet-stream"}:
        raw["sha256"] = hashlib.sha256(body).hexdigest()
        raw["body_base64_prefix"] = base64.b64encode(body[:48]).decode("ascii")
    else:
        raw["text"] = body.decode("utf-8", errors="replace")[:4000]
    return raw


def save_body(path, raw):
    body = raw.get("body", b"")
    if body:
        path.write_bytes(body)


def run_probe(out_dir):
    api_key = get_api_key()
    out_dir.mkdir(parents=True, exist_ok=True)
    fixture = out_dir / "stt_tone_fixture.wav"
    make_wav(fixture)

    metadata = {
        "created_at": now_iso(),
        "base_url": BASE_URL,
        "models": {
            "chat": CHAT_MODEL,
            "stt": STT_MODEL,
            "tts": TTS_MODEL,
            "tts_voice": TTS_VOICE,
        },
        "env_present": {
            "GROQ_API_KEY": bool(os.environ.get("GROQ_API_KEY")),
            "PROVIDER_API_KEY": bool(os.environ.get("PROVIDER_API_KEY")),
        },
        "commands": [
            "python probe_groq.py --out artifacts",
        ],
    }

    results = {"metadata": metadata, "tests": []}
    if not api_key:
        results["tests"].append(
            {
                "name": "preflight",
                "ok": False,
                "status": None,
                "error": "Neither GROQ_API_KEY nor PROVIDER_API_KEY is set.",
            }
        )
        write_json(out_dir / "results.json", results)
        return results

    tests = [
        (
            "list_models",
            lambda: request_json("GET", f"{BASE_URL}/models", api_key),
            None,
        ),
        (
            "chat_light",
            lambda: request_json(
                "POST",
                f"{BASE_URL}/chat/completions",
                api_key,
                {
                    "model": CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": "Answer tersely."},
                        {"role": "user", "content": "Return exactly: groq chat ok"},
                    ],
                    "temperature": 0,
                    "max_completion_tokens": 16,
                },
            ),
            None,
        ),
        (
            "tts",
            lambda: request_json(
                "POST",
                f"{BASE_URL}/audio/speech",
                api_key,
                {
                    "model": TTS_MODEL,
                    "voice": TTS_VOICE,
                    "input": "Groq text to speech probe. Please say: transcription check.",
                    "response_format": "wav",
                },
            ),
            out_dir / "tts_output.wav",
        ),
        (
            "stt_tone_fixture",
            lambda: multipart_request(
                f"{BASE_URL}/audio/transcriptions",
                api_key,
                {"model": STT_MODEL, "response_format": "json", "temperature": "0"},
                {"file": fixture},
            ),
            None,
        ),
    ]

    for name, fn, save_path in tests:
        raw = fn()
        if save_path and raw.get("ok"):
            save_body(save_path, raw)
        decoded = decode_body(dict(raw))
        decoded["name"] = name
        if save_path and save_path.exists():
            decoded["saved_file"] = str(save_path)
            decoded["saved_file_bytes"] = save_path.stat().st_size
        results["tests"].append(decoded)

    tts_path = out_dir / "tts_output.wav"
    if tts_path.exists():
        raw = multipart_request(
            f"{BASE_URL}/audio/transcriptions",
            api_key,
            {"model": STT_MODEL, "response_format": "json", "temperature": "0"},
            {"file": tts_path},
        )
        decoded = decode_body(dict(raw))
        decoded["name"] = "stt_tts_output"
        results["tests"].append(decoded)

    write_json(out_dir / "results.json", results)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts", help="Output artifact directory")
    args = parser.parse_args()
    results = run_probe(Path(args.out))
    summary = [
        {
            "name": test.get("name"),
            "ok": test.get("ok"),
            "status": test.get("status"),
            "elapsed_ms": test.get("elapsed_ms"),
            "body_bytes": test.get("body_bytes"),
            "error_type": test.get("error_type"),
        }
        for test in results["tests"]
    ]
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
