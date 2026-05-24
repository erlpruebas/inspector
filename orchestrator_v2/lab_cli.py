from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from .catalog_loader import discover_professions, load_catalog, profession_to_dict, validate_task_files
from .lab_contracts import LabActivation
from .lab_scheduler import build_schedule
from .task_generator import build_profession_generation_prompt
from .telegram_lab import execute_dry_run, execute_telegram_group, load_round_robin_endpoints


def main() -> int:
    parser = argparse.ArgumentParser(description="Laboratorio ciego del orchestrator v2.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("catalog", help="Resume el catalogo de ofimatica cargable.")
    list_prof = sub.add_parser("list-professions", help="Lista las profesiones descubiertas.")
    list_prof.add_argument("--base-dir", default="benchmarks/contracts")
    gen = sub.add_parser("generate-prompt", help="Genera prompt para crear una nueva profesion/tareas/assets.")
    gen.add_argument("--title", required=True)
    gen.add_argument("--description", required=True)
    gen.add_argument("--task-count", type=int, default=20)

    activate = sub.add_parser("activate", help="Crea una activacion del laboratorio.")
    activate.add_argument("--profession", default="office_general")
    activate.add_argument("--task", action="append", default=[])
    activate.add_argument("--persona", action="append", default=[])
    activate.add_argument("--speed-seconds", type=float, default=60.0)
    activate.add_argument("--speed-mode", choices=("fixed", "jitter", "burst"), default="fixed")
    activate.add_argument("--max-tasks", type=int, default=4)
    activate.add_argument("--transport", choices=("dry_run", "telegram_group_bots", "telegram_user_sessions"), default="dry_run")
    activate.add_argument("--evidence-dir", default="")
    activate.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    if args.command == "generate-prompt":
        print(build_profession_generation_prompt(args.title, args.description, args.task_count))
        return 0

    if args.command == "list-professions":
        professions = [profession_to_dict(profession) for profession in discover_professions(Path(args.base_dir))]
        print(json.dumps(professions, indent=2, ensure_ascii=False))
        return 0

    profession, tasks, personas = load_catalog(getattr(args, "profession", "office_general"))
    if args.command == "catalog":
        missing = validate_task_files(tasks)
        print(json.dumps({
            "profession": profession.id,
            "title": profession.title,
            "tasks": len(tasks),
            "personas": len(personas),
            "missing_file_tasks": missing,
        }, indent=2, ensure_ascii=False))
        return 0

    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else Path("orchestrator_v2/runtime/lab_runs") / datetime.now().strftime("%Y%m%d_%H%M%S")
    activation = LabActivation(
        id=datetime.now().strftime("lab_%Y%m%d_%H%M%S"),
        profession_id=args.profession,
        task_ids=tuple(args.task),
        persona_ids=tuple(args.persona),
        speed_seconds=args.speed_seconds,
        speed_mode=args.speed_mode,
        transport=args.transport,
        max_tasks=args.max_tasks,
        evidence_dir=evidence_dir,
    )
    schedule = build_schedule(activation, personas, tasks, seed=args.seed)
    if args.transport == "dry_run":
        written = execute_dry_run(schedule, evidence_dir)
    elif args.transport == "telegram_group_bots":
        written = execute_telegram_group(schedule, load_round_robin_endpoints(), evidence_dir)
    else:
        raise SystemExit("telegram_user_sessions queda reservado para MTProto/Telethon; aun no esta conectado.")
    (evidence_dir / "activation.json").write_text(json.dumps(activation.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "activation": activation.id,
        "profession": activation.profession_id,
        "messages": len(schedule),
        "evidence_dir": str(evidence_dir),
        "files": [str(path) for path in written],
    }, indent=2, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
