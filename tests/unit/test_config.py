from pathlib import Path

from aion.config import load_app_config


def test_load_app_config_reads_yaml_values(tmp_path: Path) -> None:
    (tmp_path / ".aion.yaml").write_text(
        "\n".join(
            [
                "provider: openai",
                "model: gpt-4.1",
                "ignore_paths:",
                "  - tests/*",
                "  - scripts/generated_*.py",
                "auto_repair_issue_types:",
                "  - hardcoded_secret",
                "auto_repair_min_confidence: 0.95",
                "sandbox_mode: file",
                "sandbox_verification_commands:",
                "  - python -c \"print('ok')\"",
                "auto_approve_verified_fixes: true",
                "rollback_on_verification_failure: false",
            ]
        ),
        encoding="utf-8",
    )

    config = load_app_config(tmp_path)

    assert config.provider == "openai"
    assert config.model == "gpt-4.1"
    assert config.ignore_paths == ["tests/*", "scripts/generated_*.py"]
    assert config.auto_repair_issue_types == ["hardcoded_secret"]
    assert config.auto_repair_min_confidence == 0.95
    assert config.sandbox_mode == "file"
    assert config.sandbox_verification_commands == ['python -c "print(\'ok\')"']
    assert config.auto_approve_verified_fixes is True
    assert config.rollback_on_verification_failure is False
