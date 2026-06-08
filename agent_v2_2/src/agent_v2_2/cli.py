from __future__ import annotations

import argparse
import logging
import sys

from .capabilities.preferences import PreferenceStore
from .capabilities.status import StatusManager
from .capabilities.voice import VoiceCapabilities

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_v2_2.cli")


def _print_preferences() -> None:
    state = PreferenceStore().load()
    print(f"voz={'on' if state.voice_enabled else 'off'}")
    print(f"altavoz={'on' if state.speaker_enabled else 'off'}")
    print(f"proveedor_voz={state.voice_provider}")
    print(f"voz_nombre={state.voice_name or '(default)'}")
    print(f"anonimizacion={'on' if state.anonymization_enabled else 'off'}")
    print(f"modo_desarrollo={'on' if state.development_mode_enabled else 'off'}")


def start_agent() -> None:
    logger.info("Iniciando Inspector Agent 2.2...")
    print("El agente se ha iniciado (smoke test).")


def check_status() -> None:
    logger.info("Comprobando estado del sistema...")
    print(StatusManager().generate_status_report())
    print("")
    _print_preferences()


def set_voice(enabled: bool) -> None:
    state = PreferenceStore().toggle_voice(enabled)
    print(f"voz={'on' if state.voice_enabled else 'off'}")


def set_speaker(enabled: bool) -> None:
    state = PreferenceStore().toggle_speaker(enabled)
    print(f"altavoz={'on' if state.speaker_enabled else 'off'}")


def set_voice_provider(provider: str) -> None:
    state = PreferenceStore().set_voice_provider(provider)
    print(f"proveedor_voz={state.voice_provider}")


def set_voice_name(voice_name: str) -> None:
    state = PreferenceStore().set_voice_name(voice_name)
    print(f"voz_nombre={state.voice_name}")


def warmup_voice() -> None:
    warmup = VoiceCapabilities().warmup()
    for key, value in warmup.items():
        print(f"{key}={'ok' if value else 'no'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspector Agent 2.2 CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    subparsers.add_parser("start", help="Inicia el agente (Telegram long-polling)")
    subparsers.add_parser("status", help="Comprueba el estado del agente y dependencias")
    subparsers.add_parser("estado", help="Alias de status")

    voice_parser = subparsers.add_parser("voz", help="Activa, desactiva o configura la voz")
    voice_sub = voice_parser.add_subparsers(dest="voice_command", required=True)
    voice_on = voice_sub.add_parser("on", help="Activa la voz")
    voice_on.set_defaults(func=lambda args: set_voice(True))
    voice_off = voice_sub.add_parser("off", help="Desactiva la voz")
    voice_off.set_defaults(func=lambda args: set_voice(False))
    voice_provider = voice_sub.add_parser("provider", help="Selecciona proveedor de voz")
    voice_provider.add_argument("provider", choices=["edge", "gemini", "elevenlabs"])
    voice_provider.set_defaults(func=lambda args: set_voice_provider(args.provider))
    voice_name = voice_sub.add_parser("name", help="Selecciona voz concreta")
    voice_name.add_argument("name")
    voice_name.set_defaults(func=lambda args: set_voice_name(args.name))
    voice_warmup = voice_sub.add_parser("warmup", help="Comprueba disponibilidad de voz")
    voice_warmup.set_defaults(func=lambda args: warmup_voice())

    speaker_parser = subparsers.add_parser("altavoz", help="Activa o desactiva el altavoz local")
    speaker_sub = speaker_parser.add_subparsers(dest="speaker_command", required=True)
    speaker_on = speaker_sub.add_parser("on", help="Activa el altavoz")
    speaker_on.set_defaults(func=lambda args: set_speaker(True))
    speaker_off = speaker_sub.add_parser("off", help="Desactiva el altavoz")
    speaker_off.set_defaults(func=lambda args: set_speaker(False))

    args = parser.parse_args()

    if args.command == "start":
        start_agent()
    elif args.command in {"status", "estado"}:
        check_status()
    elif hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
