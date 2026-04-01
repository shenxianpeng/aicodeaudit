import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from aion.cli import app
from aion.inbox import EventInbox
from aion.orchestrator import Orchestrator


def test_event_inbox_enqueue_and_mark_processed(tmp_path: Path) -> None:
    inbox = EventInbox(tmp_path / "inbox")
    event = Orchestrator().ingest_event(
        {
            "event_type": "code_scan",
            "target_file": "/tmp/demo.py",
        }
    )

    item = inbox.enqueue(event)
    result_path = inbox.result_file(item)
    result_path.write_text("{}", encoding="utf-8")
    processed = inbox.mark_processed(item, result_path)

    assert processed.status == "processed"
    assert processed.result_path == str(result_path)
    assert inbox.list_items(status="processed")[0].item_id == item.item_id


def test_cli_enqueue_list_and_process_inbox(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("aion.repair.semgrep_available", lambda: False)
    runner = CliRunner()
    inbox_root = tmp_path / "inbox"

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".aion.yaml").write_text(
        "\n".join(
            [
                "sandbox_mode: repository",
                f"sandbox_verification_commands:\n  - {sys.executable} -c \"print('inbox-ok')\"",
                "auto_approve_verified_fixes: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    target = repo_root / "service.py"
    target.write_text(Path("tests/fixtures/vulnerable/02_hardcoded_secret.py").read_text(encoding="utf-8"), encoding="utf-8")
    context = repo_root / "context.json"
    context.write_text(Path("tests/fixtures/vulnerable/02_context.json").read_text(encoding="utf-8"), encoding="utf-8")
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "event_type": "runtime_alert",
                "target_file": str(target.resolve()),
                "metadata": {
                    "repo_root": str(repo_root.resolve()),
                    "context_file": str(context.resolve()),
                },
            }
        ),
        encoding="utf-8",
    )

    enqueue = runner.invoke(app, ["enqueue-event", str(event_path), "--inbox-root", str(inbox_root), "--output", "json"])
    assert enqueue.exit_code == 0
    item = json.loads(enqueue.stdout)
    assert item["status"] == "pending"

    listed = runner.invoke(app, ["list-inbox", "--inbox-root", str(inbox_root), "--status", "pending", "--output", "json"])
    assert listed.exit_code == 0
    pending_items = json.loads(listed.stdout)
    assert len(pending_items) == 1

    processed = runner.invoke(
        app,
        ["process-inbox", "--inbox-root", str(inbox_root), "--cleanup-sandbox", "--output", "json"],
    )
    assert processed.exit_code == 0
    payload = json.loads(processed.stdout)
    assert payload["summary"]["total_events"] == 1
    assert payload["summary"]["approved_count"] == 1

    processed_list = runner.invoke(
        app,
        ["list-inbox", "--inbox-root", str(inbox_root), "--status", "processed", "--output", "json"],
    )
    processed_items = json.loads(processed_list.stdout)
    assert len(processed_items) == 1
    assert Path(processed_items[0]["result_path"]).exists()
