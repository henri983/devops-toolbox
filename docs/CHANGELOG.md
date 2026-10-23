# Changelog

All notable changes to the **DevOps Toolbox** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-23

### Added
- **Ansible Configuration Management**:
  - Full modular role architecture (`common`, `docker_host`, `monitoring_agent`).
  - Production, staging, and monitoring multi-group inventory (`ansible/inventory/hosts.yml`).
  - CIS / ANSSI baseline security configurations (`sshd` hardening, UFW default-deny, Chrony NTP).
  - Orchestration playbooks: `site.yml`, `hardening.yml`, `backup.yml`.
- **DevOps Automation Scripts**:
  - `scripts/bash/backup_postgres.sh`: Gzip PostgreSQL backup with SHA-256 integrity and automatic retention.
  - `scripts/bash/system_health_audit.sh`: Multi-metric resource health auditor with JSON output.
  - `scripts/bash/ssl_cert_checker.sh`: TLS certificate expiration alerting script.
  - `scripts/bash/docker_prune_safe.sh`: Safe Docker cleanup tool with dry-run support.
  - `scripts/python/secret_scanner.py`: Shannon entropy and regex credential leak detector.
  - `scripts/python/cloud_cost_optimizer.py`: Idle compute and unattached volume cost leak analyzer.
  - `scripts/python/log_rotator.py`: Atomic log compressor, rotational backup, and retention manager.
- **AI SysAdmin Copilot Engine**:
  - `src/ai/log_anomaly_detector.py`: Log parser, error burst detector, and statistical anomaly engine.
  - `src/ai/drift_analyzer.py`: Runtime configuration drift detection with automated Ansible remediation playbooks.
  - `src/cli.py`: Unified Click CLI interface for operational automation.
- **Testing & Quality Assurance**:
  - 34 comprehensive tests across unit, ansible, ai, and integration suites (100% pass rate).
  - GitHub Actions CI workflow for linting, security scanning (Bandit), and test verification.
- **Signed Integrity Attestation Block**:
  - Embedded cryptographically signed metadata block in `README.md`.
