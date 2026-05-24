import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel


def resample_to_16k(audio, sample_rate):
    if sample_rate == 16000:
        return audio.astype("float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    old_x = np.linspace(0.0, 1.0, num=len(audio), endpoint=False)
    new_len = int(round(len(audio) * 16000 / sample_rate))
    new_x = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
    return np.interp(new_x, old_x, audio).astype("float32")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--models-dir", required=True)
    parser.add_argument("--language", default=None)
    args = parser.parse_args()

    audio_path = Path(args.audio)
    info = sf.info(str(audio_path))
    audio, sample_rate = sf.read(str(audio_path), dtype="float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    audio_16k = resample_to_16k(audio, sample_rate)

    model = WhisperModel(
        args.model,
        device="cpu",
        compute_type="int8",
        download_root=args.models_dir,
    )
    segments, detected = model.transcribe(
        audio_16k,
        language=args.language,
        vad_filter=False,
    )
    text = "".join(segment.text for segment in segments).strip()

    payload = {
        "provider": "local",
        "model": args.model,
        "text": text,
        "language": getattr(detected, "language", None),
        "duration_s": round(info.duration, 3),
        "sample_rate": info.samplerate,
        "channels": info.channels,
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
