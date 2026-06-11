from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agent_v2_2.application import AgentApplication
from agent_v2_2.capabilities.memory import MemoryStore
from agent_v2_2.evolution import BenchmarkArena, ExperienceStore, NormalizedTask, RouterExperience
from agent_v2_2.evolution.audit import TaskRecord
from agent_v2_2.evolution.hitl import HITLController
from agent_v2_2.evolution.matrix import CapabilityMatrixBuilder
from agent_v2_2.evolution.normalization import TaskNormalizer
from agent_v2_2.evolution.training_coverage import TrainingCoverageAnalyzer
from agent_v2_2.models import OrchestratorResult, TaskRequest
from agent_v2_2.routing.builder import ContractBuilder
from agent_v2_2.routing.evolutionary import EvolutionPolicy, EvolutionarySelector


def _experience(
    index: int,
    tool_id: str,
    *,
    elapsed: float,
    score: float,
    passed: bool = True,
) -> RouterExperience:
    return RouterExperience(
        experience_id=f"exp-{tool_id}-{index}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        catalog_version=4,
        task_id=f"task-{index}",
        task_shape="calculate",
        tool_id=tool_id,
        required_capabilities=["cap_calc_filter"],
        cognitive_requirements=["multi_step_calculation"],
        elapsed_seconds=elapsed,
        objective_checks={"passed": passed, "checks": []},
        judge_scores=[
            {
                "judge": "blind-test",
                "score": score,
                "passed": passed,
                "capability_scores": {"cap_calc_filter": score},
            }
        ],
        outcome="sufficient" if passed else "insufficient",
        metadata={
            "primary_capability": "cap_calc_filter",
            "evidence_kind": "live",
        },
    )


def test_evolutionary_selector_chooses_fastest_sufficient_tool(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    store = ExperienceStore(tmp_path / "experiences.jsonl")
    store.append_many(
        [
            *[_experience(index, "router_groq_qwen32", elapsed=1.2, score=8.0) for index in range(5)],
            *[_experience(index, "worker_openrouter_deepseek32", elapsed=4.0, score=9.0) for index in range(5)],
        ]
    )
    selector = EvolutionarySelector(
        experience_store=store,
        policy=EvolutionPolicy(exploration_rate=0),
    )
    contract = ContractBuilder().build("Calcula el total de 12, 18 y 24.")

    decision = selector.select_contract(contract)
    assert decision.tool_id == "router_groq_qwen32"
    assert decision.alternatives[0] == "gemini_pro_long_context"
    assert "fastest sufficient" in decision.reason


def test_evolutionary_exploration_requires_reproducible_task(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    selector = EvolutionarySelector(
        experience_store=ExperienceStore(tmp_path / "experiences.jsonl"),
        policy=EvolutionPolicy(exploration_rate=1),
    )
    human_request = ContractBuilder().build("Calcula el total de 12, 18 y 24.")
    benchmark_request = human_request.model_copy(
        update={"metadata": {**human_request.metadata, "reproducible": True}}
    )

    assert selector._should_explore(human_request) is False
    assert selector._should_explore(benchmark_request) is True


def test_benchmark_arena_runs_every_compatible_tool(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    contract = ContractBuilder().build("Calcula el total de 12, 18 y 24.")
    task = NormalizedTask(
        task_id="all-tools",
        title="All tools",
        source_path=Path("synthetic.json"),
        prompt=contract.normalized_request,
        primary_capability="cap_calc_filter",
        compatible_tools=["router_groq_qwen32", "worker_openrouter_deepseek32"],
        objective_checks=["contains:54"],
        judge_rubric={"correctness": 10},
        task_shape="calculate",
        contract=contract.model_dump(mode="json"),
    )

    def executor(task, tool_id, contract):
        del task, contract
        return OrchestratorResult(
            ok=True,
            tool_id=tool_id,
            tier="general",
            output="54",
            elapsed_seconds=1.0,
            metadata={"evidence_kind": "live"},
        )

    arena = BenchmarkArena(
        experience_store=ExperienceStore(tmp_path / "arena.jsonl")
    )
    report = arena.run(
        [task],
        executor=executor,
        all_compatible_tools=True,
    )
    assert report.total_runs == 2
    assert report.passed_runs == 2
    assert set(report.tool_counts) == {
        "router_groq_qwen32",
        "worker_openrouter_deepseek32",
    }


def test_application_rolls_back_after_provider_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    store = ExperienceStore(tmp_path / "experiences.jsonl")
    store.append_many(
        [
            *[_experience(index, "router_groq_qwen32", elapsed=1.0, score=8.0) for index in range(5)],
            *[_experience(index, "worker_openrouter_deepseek32", elapsed=3.0, score=8.0) for index in range(5)],
        ]
    )
    selector = EvolutionarySelector(
        experience_store=store,
        policy=EvolutionPolicy(exploration_rate=0),
    )
    attempts: list[str] = []

    def executor(request, decision):
        del request
        attempts.append(decision.tool_id)
        if decision.tool_id == "router_groq_qwen32":
            return OrchestratorResult(
                ok=False,
                tool_id=decision.tool_id,
                tier=decision.tier,
                error="429 rate limit",
                metadata={"evidence_kind": "live"},
            )
        return OrchestratorResult(
            ok=True,
            tool_id=decision.tool_id,
            tier=decision.tier,
            output="54",
            metadata={"evidence_kind": "live"},
        )

    application = AgentApplication(
        selector=selector,
        executor=executor,
        memory_store=MemoryStore(tmp_path / "memory"),
        experience_store=store,
    )
    contract = ContractBuilder().build("Calcula el total de 12, 18 y 24.")
    request = TaskRequest(
        user_id="1",
        thread_id="1",
        text=contract.normalized_request,
    )

    result = application.handle(request, contract)
    assert result.ok is True
    assert attempts == ["router_groq_qwen32", "gemini_pro_long_context"]
    saved = store.load()[-1]
    assert saved.tool_id == "gemini_pro_long_context"
    assert saved.metadata["attempted_tools"] == attempts


def test_hitl_controller_tracks_battery_and_feedback(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AGENT_WORKSPACE_ROOT", str(tmp_path))
    tasks_path = tmp_path / "hitl.json"
    tasks_path.write_text(
        """
        [
          {
            "id": "hitl-1",
            "title": "Remember a fact",
            "prompt": "Dime el CIF que aparece en el texto preparado.",
            "skills": ["agenda"],
            "rubric": {"correctness": 10}
          },
          {
            "id": "hitl-2",
            "title": "Draft a reply",
            "prompt": "Redacta una respuesta breve y educada.",
            "skills": ["draft"],
            "rubric": {"correctness": 10}
          }
        ]
        """.strip(),
        encoding="utf-8",
    )
    store = ExperienceStore(tmp_path / "experiences.jsonl")
    store.append(
        RouterExperience(
            experience_id="request-1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            catalog_version=4,
            task_id="request-1",
            task_shape="answer",
            tool_id="router_groq_qwen32",
            metadata={"evidence_kind": "live"},
        )
    )
    controller = HITLController(
        tasks_path=tasks_path,
        state_path=tmp_path / "state.json",
        trials_path=tmp_path / "trials.jsonl",
        experience_store=store,
    )

    first = controller.start(123)
    assert first.task_id == "hitl-1"
    assert controller.next(123).task_id == "hitl-2"
    assert controller.repeat(123).task_id == "hitl-2"
    trial = controller.begin_trial(123, first)
    controller.link_result(
        trial.trial_id,
        experience_id="request-1",
        tool_id="router_groq_qwen32",
        elapsed_seconds=1.4,
    )
    assert controller.record_feedback(123, "yes", friction="low") is True
    assert controller.record_annotation(
        123,
        correction="La respuesta debia ser mas breve.",
    )
    assert controller.report()["useful"] == 1.0
    assert store.load()[0].user_feedback == "yes"
    assert (
        store.load()[0].metadata["hitl_correction"]
        == "La respuesta debia ser mas breve."
    )


def test_matrix_excludes_unavailable_and_keeps_capability_scores_separate(
    tmp_path: Path,
) -> None:
    store = ExperienceStore(tmp_path / "matrix.jsonl")
    valid = _experience(1, "router_groq_qwen32", elapsed=1.0, score=9.0)
    valid.required_capabilities = ["cap_calc_filter", "cap_verify"]
    valid.judge_scores[0]["capability_scores"] = {
        "cap_calc_filter": 9.0,
        "cap_verify": 4.0,
    }
    unavailable = _experience(2, "router_groq_qwen32", elapsed=0.1, score=10.0)
    unavailable.metadata["evidence_kind"] = "unavailable"
    store.append_many([valid, unavailable])

    report = CapabilityMatrixBuilder(store).build()
    cells = {cell.capability: cell for cell in report.cells}
    assert cells["cap_calc_filter"].samples == 1
    assert cells["cap_calc_filter"].mean_score == 9.0
    assert cells["cap_verify"].mean_score == 4.0


def test_matrix_excludes_invalidated_evidence(tmp_path: Path) -> None:
    store = ExperienceStore(tmp_path / "matrix.jsonl")
    invalid = _experience(
        1,
        "router_groq_qwen32",
        elapsed=1.0,
        score=1.0,
        passed=False,
    )
    store.append(invalid)

    assert store.invalidate([invalid.experience_id], "adapter truncation") == 1

    report = CapabilityMatrixBuilder(store).build()
    assert report.cells == []
    loaded = store.load()[0]
    assert loaded.metadata["evidence_invalidated"] is True
    assert loaded.metadata["invalidation_reason"] == "adapter truncation"

    assert store.restore([invalid.experience_id]) == 1
    restored = CapabilityMatrixBuilder(store).build()
    assert len(restored.cells) == 1
    assert "evidence_invalidated" not in store.load()[0].metadata


def test_experience_store_exports_sanitized_portable_seed(
    tmp_path: Path,
) -> None:
    store = ExperienceStore(tmp_path / "source.jsonl")
    valid = _experience(1, "router_groq_qwen32", elapsed=1.0, score=9.0)
    valid.metadata["source_summary"] = r"D:\private\summary.json"
    invalid = _experience(2, "router_groq_qwen32", elapsed=1.0, score=9.0)
    invalid.metadata["evidence_invalidated"] = True
    store.append_many([valid, invalid])

    destination = tmp_path / "seed.jsonl"
    assert store.export_portable_seed(destination) == 1
    payload = destination.read_text(encoding="utf-8")
    assert "source_summary" not in payload
    assert "D:\\private" not in payload
    assert '"comment": ""' in payload
    assert '"portable_seed": true' in payload


def test_training_coverage_requires_passing_judged_live_evidence(
    tmp_path: Path,
) -> None:
    store = ExperienceStore(tmp_path / "coverage.jsonl")
    store.append(_experience(1, "router_groq_qwen32", elapsed=1.0, score=6.0, passed=False))
    matrix = CapabilityMatrixBuilder(store).build()
    task = NormalizedTask(
        task_id="coverage",
        title="Coverage",
        source_path=Path("synthetic.json"),
        prompt="Calcula.",
        primary_capability="cap_calc_filter",
        compatible_tools=["router_groq_qwen32"],
    )

    report = TrainingCoverageAnalyzer().analyze([task], matrix)
    assert report.expected_pairs == 1
    assert report.demonstrated_pairs == 0
    assert report.missing_demonstrations()[0].tool_id == "router_groq_qwen32"


def test_missing_information_task_is_not_file_creation() -> None:
    task = TaskNormalizer().normalize_record(
        TaskRecord(
            task_id="clarify",
            title="Clarify missing budget data",
            source_path=Path("synthetic.json"),
            prompt="Prepara el presupuesto nuevo para el cliente.",
            skills=["ask_for_missing_information"],
            expected_keys=["cliente", "conceptos", "importes"],
        )
    )

    assert task.primary_capability == "cap_transform_redact"


def test_multi_file_comparison_uses_compare_capability() -> None:
    task = TaskNormalizer().normalize_record(
        TaskRecord(
            task_id="compare",
            title="Compare budgets",
            source_path=Path("synthetic.json"),
            prompt="Compara presupuesto_A.pdf con presupuesto_B.pdf.",
            required_files=["presupuesto_A.pdf", "presupuesto_B.pdf"],
        )
    )

    assert task.primary_capability == "cap_compare"


def test_structured_file_modification_does_not_require_code_execution() -> None:
    task = TaskNormalizer().normalize_record(
        TaskRecord(
            task_id="modify-json",
            title="Modify JSON",
            source_path=Path("synthetic.json"),
            prompt="Actualiza customer.json y crea customer_updated.json.",
            required_files=["customer.json"],
            expected_operation="artifact_modification",
            skills=["write_file"],
        )
    )

    required = set(task.contract["execute"]["instrumental_capabilities"])
    assert "write_file" in required
    assert "code_execution" not in required
    assert "gemini_flash_35" in task.compatible_tools
