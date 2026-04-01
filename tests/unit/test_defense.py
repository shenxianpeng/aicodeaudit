import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from aion.cli import app
from aion.config import AppConfig
from aion.defense import RuntimeDefensePlanner
from aion.models import ContextProfile
from aion.orchestrator import Orchestrator
from aion.repair import IncidentDetector


def test_runtime_defense_planner_prioritizes_edge_controls() -> None:
    target = Path("tests/fixtures/vulnerable/02_hardcoded_secret.py")
    context = ContextProfile(**json.loads(Path("tests/fixtures/vulnerable/02_context.json").read_text(encoding="utf-8")))
    incidents = IncidentDetector().detect(target, context)
    event = Orchestrator().ingest_event({"event_type": "runtime_alert", "target_file": str(target.resolve())})

    plan = RuntimeDefensePlanner().plan(event, incidents)

    assert [action.action_type for action in plan.actions[:2]] == ["gateway_block", "waf_rule"]
    assert any(action.action_type == "code_patch" for action in plan.actions)


def test_cli_plan_defense_reads_orchestration_result(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("aion.repair.semgrep_available", lambda: False)
    repo_root = tmp_path / "defense-repo"
    repo_root.mkdir()
    target = repo_root / "service.py"
    target.write_text(Path("tests/fixtures/vulnerable/03_missing_auth_decorator.py").read_text(encoding="utf-8"), encoding="utf-8")
    context_path = repo_root / "context.json"
    context_path.write_text(Path("tests/fixtures/vulnerable/03_context.json").read_text(encoding="utf-8"), encoding="utf-8")

    orchestrator = Orchestrator.from_config(
        AppConfig(
            sandbox_mode="repository",
            sandbox_verification_commands=[f'{sys.executable} -c "print(\'defense-ok\')"'],
        )
    )
    event = orchestrator.ingest_event(
        {
            "event_type": "runtime_alert",
            "target_file": str(target.resolve()),
            "metadata": {
                "repo_root": str(repo_root.resolve()),
                "context_file": str(context_path.resolve()),
            },
        }
    )
    context = ContextProfile(**json.loads(context_path.read_text(encoding="utf-8")))
    result = orchestrator.process_event(event, context, repo_root=repo_root.resolve())
    result_path = tmp_path / "orchestration.json"
    result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    runner = CliRunner()
    response = runner.invoke(app, ["plan-defense", str(result_path), "--output", "json"])

    assert response.exit_code == 0
    payload = json.loads(response.stdout)
    assert payload["strategy"] == "runtime_containment_first"
    assert any(action["action_type"] == "feature_flag" for action in payload["actions"])
    orchestrator.cleanup_sandbox(result)
