"""AI SysAdmin Copilot - Ansible Configuration Drift & Compliance Analyzer.

Author: henri983 (henrinyame2001@gmail.com)
Part of DevOps Toolbox Foundations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DriftItem:
    parameter: str
    expected_value: Any
    actual_value: Any
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    remediation_task: str


@dataclass
class DriftReport:
    hostname: str
    compliance_score: float  # 0.0 to 1.0 (1.0 = perfect compliance)
    drift_score: float  # 0.0 to 1.0 (0.0 = zero drift)
    is_drifted: bool
    drift_items: List[DriftItem] = field(default_factory=list)
    remediation_playbook_snippet: str = ""


class DriftAnalyzer:
    """Analyzes declared Ansible baseline states against actual runtime host facts."""

    SEVERITY_SCORES = {
        "LOW": 0.05,
        "MEDIUM": 0.15,
        "HIGH": 0.30,
        "CRITICAL": 0.50,
    }

    def __init__(self, drift_threshold: float = 0.20) -> None:
        self.drift_threshold = drift_threshold

    def compare_state(
        self,
        hostname: str,
        expected_state: Dict[str, Any],
        actual_state: Dict[str, Any],
    ) -> DriftReport:
        """Compare expected configuration dictionary with actual collected facts."""
        drift_items: List[DriftItem] = []

        # 1. Check Packages
        exp_packages = set(expected_state.get("packages", []))
        act_packages = set(actual_state.get("packages", []))
        missing_pkgs = exp_packages - act_packages
        for pkg in missing_pkgs:
            drift_items.append(
                DriftItem(
                    parameter=f"package.{pkg}",
                    expected_value="present",
                    actual_value="absent",
                    severity="HIGH",
                    remediation_task=f"ansible.builtin.package: name={pkg} state=present",
                )
            )

        # 2. Check Open / Allowed Ports
        exp_ports = set(expected_state.get("allowed_ports", []))
        act_ports = set(actual_state.get("listening_ports", []))
        unauthorized_ports = act_ports - exp_ports
        for port in unauthorized_ports:
            drift_items.append(
                DriftItem(
                    parameter=f"port.{port}",
                    expected_value="closed/blocked",
                    actual_value="listening",
                    severity="CRITICAL",
                    remediation_task=f"community.general.ufw: port={port} rule=deny",
                )
            )

        # 3. Check SSH Hardening Parameters
        exp_ssh = expected_state.get("sshd", {})
        act_ssh = actual_state.get("sshd", {})
        for param, exp_val in exp_ssh.items():
            act_val = act_ssh.get(param)
            if str(act_val).lower() != str(exp_val).lower():
                drift_items.append(
                    DriftItem(
                        parameter=f"sshd.{param}",
                        expected_value=exp_val,
                        actual_value=act_val,
                        severity="HIGH",
                        remediation_task=f"ansible.builtin.lineinfile: path=/etc/ssh/sshd_config regexp='^{param}' line='{param} {exp_val}'",
                    )
                )

        # 4. Check Sysctl Security Parameters
        exp_sysctl = expected_state.get("sysctl", {})
        act_sysctl = actual_state.get("sysctl", {})
        for key, exp_val in exp_sysctl.items():
            act_val = act_sysctl.get(key)
            if str(act_val) != str(exp_val):
                drift_items.append(
                    DriftItem(
                        parameter=f"sysctl.{key}",
                        expected_value=exp_val,
                        actual_value=act_val,
                        severity="MEDIUM",
                        remediation_task=f"ansible.posix.sysctl: name={key} value='{exp_val}' state=present",
                    )
                )

        # Calculate total accumulated drift score
        raw_drift = sum(self.SEVERITY_SCORES.get(item.severity, 0.1) for item in drift_items)
        drift_score = min(1.0, round(raw_drift, 4))
        compliance_score = round(1.0 - drift_score, 4)
        is_drifted = drift_score >= self.drift_threshold

        # Generate snippet
        remediation_lines = [
            f"# Auto-generated remediation for host {hostname}",
            "- name: Remediate Configuration Drift",
            "  hosts: " + hostname,
            "  become: true",
            "  tasks:",
        ]
        for item in drift_items:
            remediation_lines.append(f"    - name: Fix {item.parameter}")
            remediation_lines.append(f"      {item.remediation_task}")

        snippet = "\n".join(remediation_lines) if drift_items else "# No drift detected. Host is compliant."

        return DriftReport(
            hostname=hostname,
            compliance_score=compliance_score,
            drift_score=drift_score,
            is_drifted=is_drifted,
            drift_items=drift_items,
            remediation_playbook_snippet=snippet,
        )
