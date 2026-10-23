# DevOps Scripts Reference

This document provides a comprehensive operational guide for all automated scripts included in the **DevOps Toolbox**.

---

## 1. Shell Scripts (`scripts/bash/`)

### `backup_postgres.sh`
- **Purpose**: Creates compressed, timestamped PostgreSQL dumps with SHA-256 verification and automatic 7-day retention purging.
- **Error Handling**: `set -euo pipefail` and an active `ERR` trap that purges incomplete files on abnormal exit.
- **Usage**:
  ```bash
  BACKUP_DIR="/var/backups/postgres" PGDATABASE="my_db" ./scripts/bash/backup_postgres.sh
  ```

### `system_health_audit.sh`
- **Purpose**: Collects load average, RAM percentage, root disk usage, and zombie processes.
- **Output Formats**: Human-readable terminal output (`--text`) or machine-parseable JSON (`--json`).
- **Usage**:
  ```bash
  ./scripts/bash/system_health_audit.sh --json
  ```

### `ssl_cert_checker.sh`
- **Purpose**: Queries remote TLS/SSL certificates and alerts on impending expiration.
- **Exit Codes**:
  - `0`: Certificate healthy (> 30 days).
  - `1`: WARNING threshold reached (<= 30 days).
  - `2`: CRITICAL threshold reached (<= 7 days) or connection error.
- **Usage**:
  ```bash
  ./scripts/bash/ssl_cert_checker.sh github.com 443
  ```

### `docker_prune_safe.sh`
- **Purpose**: Safely purges stopped containers, dangling images, and unused bridge networks while preserving named persistent volumes.
- **Usage**:
  ```bash
  # Dry-run review
  ./scripts/bash/docker_prune_safe.sh --dry-run

  # Execute pruning
  ./scripts/bash/docker_prune_safe.sh --force
  ```

---

## 2. Python Automation (`scripts/python/`)

### `secret_scanner.py`
- **Purpose**: Scans codebases and configurations for leaked AWS keys, JWTs, private keys, and high-entropy secrets using Shannon entropy calculation.
- **Usage**:
  ```bash
  python -m src.cli scan-secrets --path . --entropy 4.2
  ```

### `cloud_cost_optimizer.py`
- **Purpose**: Identifies idle compute instances (< 5% CPU) and unattached block storage volumes, calculating potential monthly USD savings.
- **Usage**:
  ```bash
  python -m src.cli optimize-costs
  ```

### `log_rotator.py`
- **Purpose**: Evaluates log file sizes, performs atomic gzip rotation with sequence numbering (`.1.gz`, `.2.gz`), truncates active logs without closing open descriptors, and purges expired archives.
