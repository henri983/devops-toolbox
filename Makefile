.PHONY: help install lint test security audit-playbooks run-cli

help:
	@echo "DevOps Toolbox - Automation and Ansible Management"
	@echo "Available commands:"
	@echo "  make install         Install Python dependencies"
	@echo "  make lint            Run linters (ruff, ansible-lint checks)"
	@echo "  make test            Run complete test suite (unit, ansible, ai, integration)"
	@echo "  make security        Run security vulnerability scan with bandit"
	@echo "  make audit-playbooks Verify YAML syntax of all Ansible playbooks"
	@echo "  make run-cli         Launch AI SysAdmin Copilot CLI"

install:
	pip install -r requirements/base.txt -r requirements/test.txt

lint:
	ruff check .
	ruff format --check .

test:
	pytest -v --cov=src --cov=scripts/python --cov-report=term-missing

security:
	bandit -r src/ scripts/python/ -ll

audit-playbooks:
	python -m src.cli audit-playbooks --inventory ansible/inventory/hosts.yml

run-cli:
	python -m src.cli --help
