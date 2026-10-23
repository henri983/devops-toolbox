"""Tests for Ansible syntax, playbook structure, and role task integrity."""

from __future__ import annotations

from pathlib import Path
import yaml
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ANSIBLE_DIR = REPO_ROOT / "ansible"


def test_ansible_inventory_valid_yaml() -> None:
    inv_file = ANSIBLE_DIR / "inventory" / "hosts.yml"
    assert inv_file.exists(), f"Missing inventory file: {inv_file}"

    with inv_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "all" in data
    children = data["all"]["children"]
    assert "production" in children
    assert "staging" in children
    assert "monitoring" in children


def test_ansible_group_vars_valid() -> None:
    vars_file = ANSIBLE_DIR / "inventory" / "group_vars" / "all.yml"
    assert vars_file.exists()

    with vars_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "sshd_port" in data
    assert "firewall_allowed_tcp_ports" in data
    assert 2222 in data["firewall_allowed_tcp_ports"]


@pytest.mark.parametrize(
    "role_name",
    ["common", "docker_host", "monitoring_agent"],
)
def test_ansible_roles_tasks_valid(role_name: str) -> None:
    task_file = ANSIBLE_DIR / "roles" / role_name / "tasks" / "main.yml"
    assert task_file.exists(), f"Missing task file for role {role_name}"

    with task_file.open("r", encoding="utf-8") as f:
        tasks = yaml.safe_load(f)

    assert isinstance(tasks, list), f"Tasks in {role_name} should be a list"
    assert len(tasks) > 0
    for task in tasks:
        assert "name" in task, f"Task missing 'name' in role {role_name}"


@pytest.mark.parametrize(
    "playbook_name",
    ["site.yml", "hardening.yml", "backup.yml"],
)
def test_ansible_playbooks_structure(playbook_name: str) -> None:
    pb_file = ANSIBLE_DIR / "playbooks" / playbook_name
    assert pb_file.exists(), f"Missing playbook {playbook_name}"

    with pb_file.open("r", encoding="utf-8") as f:
        plays = yaml.safe_load(f)

    assert isinstance(plays, list), f"Playbook {playbook_name} must be a list of plays"
    for play in plays:
        assert "name" in play
        assert "hosts" in play
