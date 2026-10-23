"""Unified Command Line Interface for DevOps Toolbox and AI SysAdmin Copilot.

Author: henri983 (henrinyame2001@gmail.com)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from scripts.python.cloud_cost_optimizer import CloudCostOptimizer
from scripts.python.secret_scanner import SecretScanner
from src.ai.drift_analyzer import DriftAnalyzer
from src.ai.log_anomaly_detector import LogAnomalyDetector


@click.group()
@click.version_option(version="1.0.0", prog_name="devops-toolbox")
def main() -> None:
    """DevOps Toolbox - Production Automation & AI SysAdmin Suite."""


@main.command(name="scan-secrets")
@click.option("--path", "-p", default=".", help="Target path to scan for secrets.")
@click.option("--entropy", "-e", default=4.2, help="Shannon entropy threshold.")
def scan_secrets_cmd(path: str, entropy: float) -> None:
    """Scan directory or file for leaked credentials and high-entropy secrets."""
    target = Path(path)
    scanner = SecretScanner(entropy_threshold=entropy)
    click.echo(f"[*] Scanning {target.resolve()} for credential leaks...")

    if target.is_file():
        findings = scanner.scan_file(target)
    else:
        findings = scanner.scan_directory(target)

    if not findings:
        click.secho("[+] Scan complete. Zero secrets detected!", fg="green")
        sys.exit(0)

    click.secho(f"[!] Warning: {len(findings)} potential secret(s) found:", fg="yellow", bold=True)
    for f in findings:
        click.echo(f"  - [{f.secret_type}] {f.file_path}:{f.line_number} (Entropy: {f.entropy}) -> {f.sample_masked}")
    sys.exit(1)


@main.command(name="analyze-logs")
@click.option("--file", "-f", "log_file", required=True, help="Path to server log file.")
@click.option("--threshold", "-t", default=0.70, help="Anomaly risk threshold (0.0 to 1.0).")
def analyze_logs_cmd(log_file: str, threshold: float) -> None:
    """Analyze log file with AI SysAdmin Copilot for failure spikes and anomalies."""
    target = Path(log_file)
    if not target.exists():
        click.secho(f"[-] File not found: {log_file}", fg="red")
        sys.exit(1)

    lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
    detector = LogAnomalyDetector(anomaly_threshold=threshold)
    report = detector.analyze_logs(lines)

    click.echo(f"[*] Evaluated {report.total_lines} lines:")
    click.echo(f"    - Errors: {report.error_count} | Warnings: {report.warning_count}")
    click.echo(f"    - Anomaly Score: {report.anomaly_score:.2f} (Threshold: {threshold:.2f})")
    click.echo(f"    - Burst Detected: {report.burst_detected}")

    if report.is_anomaly:
        click.secho("[!] AI ALERT: Log anomaly detected!", fg="red", bold=True)
        for r in report.reasons:
            click.echo(f"    * Reason: {r}")
        for rec in report.recommendations:
            click.echo(f"    * Recommendation: {rec}")
        sys.exit(2)
    else:
        click.secho("[+] Log behavior is nominal.", fg="green")


@main.command(name="check-drift")
@click.option("--host", default="app-prod-01.infra.internal", help="Hostname to audit.")
def check_drift_cmd(host: str) -> None:
    """Compare declared Ansible state against simulated host runtime facts."""
    expected = {
        "packages": ["ufw", "fail2ban", "chrony", "curl"],
        "allowed_ports": [2222, 80, 443],
        "sshd": {"PermitRootLogin": "no", "PasswordAuthentication": "no"},
        "sysctl": {"net.ipv4.ip_forward": 0},
    }
    # Simulated runtime facts with minor drift
    actual = {
        "packages": ["ufw", "fail2ban", "chrony"],  # missing curl
        "listening_ports": [2222, 80, 443, 8080],  # unauthorized 8080
        "sshd": {"PermitRootLogin": "no", "PasswordAuthentication": "no"},
        "sysctl": {"net.ipv4.ip_forward": 0},
    }

    analyzer = DriftAnalyzer(drift_threshold=0.20)
    report = analyzer.compare_state(host, expected, actual)

    click.echo(f"[*] Drift Audit for Host: {report.hostname}")
    click.echo(f"    - Compliance Score: {report.compliance_score * 100:.1f}%")
    click.echo(f"    - Drift Score: {report.drift_score:.2f}")

    if report.is_drifted:
        click.secho("[!] Host has drifted from declared baseline:", fg="yellow", bold=True)
        for item in report.drift_items:
            click.echo(f"    - [{item.severity}] {item.parameter}: expected '{item.expected_value}', got '{item.actual_value}'")
        click.echo("\nRemediation Playbook Snippet:")
        click.echo(report.remediation_playbook_snippet)
    else:
        click.secho("[+] Host configuration is compliant with baseline.", fg="green")


@main.command(name="audit-playbooks")
@click.option("--inventory", "-i", default="ansible/inventory/hosts.yml", help="Path to inventory YAML.")
def audit_playbooks_cmd(inventory: str) -> None:
    """Validate YAML syntax and structure of playbooks and inventory."""
    inv_path = Path(inventory)
    if not inv_path.exists():
        click.secho(f"[-] Inventory not found: {inventory}", fg="red")
        sys.exit(1)

    try:
        with inv_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        click.secho(f"[+] Inventory {inventory} is valid YAML ({len(data.get('all', {}).get('children', {}))} group(s))", fg="green")
    except Exception as e:
        click.secho(f"[-] YAML syntax error in {inventory}: {e}", fg="red")
        sys.exit(1)


@main.command(name="optimize-costs")
def optimize_costs_cmd() -> None:
    """Analyze sample cloud instances and volumes for cost waste."""
    instances = [
        {"id": "i-01a2b3c4", "instance_type": "t3.large", "avg_cpu_percent": 2.1, "state": "running"},
        {"id": "i-05d6e7f8", "instance_type": "m5.large", "avg_cpu_percent": 65.4, "state": "running"},
    ]
    volumes = [
        {"id": "vol-09a8b7c6", "size_gb": 100, "status": "available"},
        {"id": "vol-01122334", "size_gb": 50, "status": "in-use"},
    ]

    optimizer = CloudCostOptimizer()
    summary = optimizer.run_optimization_audit(instances, volumes)

    click.echo(f"[*] Evaluated {summary.total_resources_evaluated} resources.")
    click.echo(f"    - Identified idle/waste resources: {summary.idle_resources_count}")
    click.secho(
        f"    - Total potential monthly savings: ${summary.total_potential_monthly_savings_usd}/month",
        fg="green",
        bold=True,
    )
    for leak in summary.leaks:
        click.echo(f"    * [{leak.resource_type}] {leak.resource_id}: {leak.reason} (Save ${leak.estimated_monthly_saving_usd}/mo)")


if __name__ == "__main__":
    main()
