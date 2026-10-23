"""Integration tests for DevOps Toolbox CLI commands."""

from __future__ import annotations

from pathlib import Path
from click.testing import CliRunner

from src.cli import main


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "DevOps Toolbox" in result.output


def test_cli_audit_playbooks() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["audit-playbooks", "--inventory", "ansible/inventory/hosts.yml"])
    assert result.exit_code == 0
    assert "is valid YAML" in result.output


def test_cli_scan_secrets_clean_directory(temp_dir: Path) -> None:
    runner = CliRunner()
    test_file = temp_dir / "safe.py"
    test_file.write_text("API_PORT = 3000\nDEBUG = False\n")

    result = runner.invoke(main, ["scan-secrets", "--path", str(temp_dir)])
    assert result.exit_code == 0
    assert "Zero secrets detected" in result.output


def test_cli_analyze_logs_anomaly(temp_dir: Path) -> None:
    runner = CliRunner()
    log_file = temp_dir / "error.log"
    log_file.write_text(
        "2026-10-23T20:00:01 [CRITICAL] Kernel out of memory\n"
        "2026-10-23T20:00:02 [ERROR] Database crash recovery failed\n"
        "2026-10-23T20:00:03 [ERROR] Unhandled socket timeout\n"
        "2026-10-23T20:00:04 [ERROR] Container exited with status 137\n"
        "2026-10-23T20:00:05 [ERROR] Service supervisor killed\n"
    )

    result = runner.invoke(main, ["analyze-logs", "--file", str(log_file), "--threshold", "0.50"])
    assert result.exit_code == 2
    assert "AI ALERT" in result.output


def test_cli_check_drift() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["check-drift", "--host", "test-server"])
    assert result.exit_code == 0
    assert "Drift Audit for Host" in result.output
    assert "Remediation Playbook Snippet" in result.output


def test_cli_optimize_costs() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["optimize-costs"])
    assert result.exit_code == 0
    assert "Total potential monthly savings" in result.output
