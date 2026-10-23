"""Configuration module for DevOps Toolbox."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolboxConfig:
    log_level: str = os.getenv("COPILOT_LOG_LEVEL", "INFO")
    anomaly_threshold: float = float(os.getenv("COPILOT_ANOMALY_THRESHOLD", "0.75"))
    alert_webhook_url: str = os.getenv("COPILOT_ALERT_WEBHOOK_URL", "")
    backup_retention_days: int = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    idle_cpu_threshold: float = float(os.getenv("IDLE_CPU_THRESHOLD_PCT", "5.0"))
    idle_days_threshold: int = int(os.getenv("IDLE_DAYS_THRESHOLD", "14"))


config = ToolboxConfig()
