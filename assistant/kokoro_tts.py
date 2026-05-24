from __future__ import annotations

import argparse
import json
from pathlib import Path

import soundfile as sf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--voices-path", required=True)
    parser.add_argument("--voice", default="ef_dora")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--language", default="es")
    args = parser.parse_args()

    from kokoro_onnx import Kokoro

    pipeline = Kokoro(args.model_path, args.voices_path)
    audio, sample_rate = pipeline.create(
        args.text,
        voice=args.voice,
        speed=args.speed,
        lang=args.language,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output, audio, sample_rate)
    print(json.dumps({
        "output": str(output),
        "voice": args.voice,
        "sample_rate": sample_rate,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
