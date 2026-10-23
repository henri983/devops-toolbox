"""Tests for AI SysAdmin Copilot - Drift Analyzer."""

from __future__ import annotations

from src.ai.drift_analyzer import DriftAnalyzer


def test_compliant_host_state(drift_analyzer: DriftAnalyzer) -> None:
    expected = {
        "packages": ["ufw", "fail2ban", "chrony"],
        "allowed_ports": [2222, 443],
        "sshd": {"PermitRootLogin": "no"},
    }
    actual = {
        "packages": ["ufw", "fail2ban", "chrony"],
        "listening_ports": [2222, 443],
        "sshd": {"PermitRootLogin": "no"},
    }
    report = drift_analyzer.compare_state("host-prod-01", expected, actual)
    assert report.is_drifted is False
    assert report.drift_score == 0.0
    assert report.compliance_score == 1.0
    assert len(report.drift_items) == 0


def test_drift_detected_on_missing_package_and_open_port(drift_analyzer: DriftAnalyzer) -> None:
    expected = {
        "packages": ["ufw", "fail2ban", "chrony"],
        "allowed_ports": [2222, 443],
        "sshd": {"PermitRootLogin": "no"},
    }
    actual = {
        "packages": ["ufw"],  # missing fail2ban, chrony
        "listening_ports": [2222, 443, 8080],  # unauthorized 8080
        "sshd": {"PermitRootLogin": "yes"},  # insecure drift
    }
    report = drift_analyzer.compare_state("host-prod-01", expected, actual)
    assert report.is_drifted is True
    assert report.drift_score > 0.20
    assert report.compliance_score < 0.80

    params = [item.parameter for item in report.drift_items]
    assert "package.fail2ban" in params
    assert "package.chrony" in params
    assert "port.8080" in params
    assert "sshd.PermitRootLogin" in params


def test_remediation_snippet_generation(drift_analyzer: DriftAnalyzer) -> None:
    expected = {"packages": ["htop"]}
    actual = {"packages": []}
    report = drift_analyzer.compare_state("host-01", expected, actual)
    assert "Remediate Configuration Drift" in report.remediation_playbook_snippet
    assert "name=htop state=present" in report.remediation_playbook_snippet
