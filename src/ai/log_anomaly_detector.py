"""AI SysAdmin Copilot - Intelligent Log Anomaly & Failure Spike Detector.

Author: henri983 (henrinyame2001@gmail.com)
Part of DevOps Toolbox Foundations
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class LogEntry:
    timestamp: Optional[datetime]
    level: str
    component: str
    message: str
    raw: str


@dataclass
class AnomalyReport:
    total_lines: int
    error_count: int
    warning_count: int
    anomaly_score: float  # 0.0 to 1.0
    is_anomaly: bool
    burst_detected: bool
    unique_error_types: int
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class LogAnomalyDetector:
    """Detects behavioral shifts, error bursts, and unknown error anomalies in server logs."""

    SEVERITY_WEIGHTS = {
        "EMERG": 1.0,
        "ALERT": 0.95,
        "CRIT": 0.9,
        "ERROR": 0.75,
        "WARN": 0.35,
        "WARNING": 0.35,
        "INFO": 0.05,
        "DEBUG": 0.01,
    }

    # Common log regex parser (supports ISO 8601, syslog, or python-style logs)
    LOG_REGEX = re.compile(
        r"^(?:(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+)?"
        r"(?:\[?(?P<level>EMERG|ALERT|CRIT|CRITICAL|ERROR|WARN|WARNING|INFO|DEBUG)\]?\s+)?"
        r"(?:\[?(?P<component>[\w\.\-]+)\]?:\s*)?"
        r"(?P<message>.*)$",
        re.IGNORECASE,
    )

    def __init__(self, anomaly_threshold: float = 0.70) -> None:
        self.anomaly_threshold = anomaly_threshold

    def parse_line(self, line: str) -> LogEntry:
        """Parse a single log string into a structured LogEntry."""
        line_clean = line.strip()
        match = self.LOG_REGEX.match(line_clean)
        if not match:
            return LogEntry(
                timestamp=None,
                level="INFO",
                component="system",
                message=line_clean,
                raw=line_clean,
            )

        data = match.groupdict()
        level_str = (data.get("level") or "INFO").upper()
        if level_str == "CRITICAL":
            level_str = "CRIT"

        ts: Optional[datetime] = None
        if data.get("timestamp"):
            try:
                # Basic ISO parse
                ts_str = data["timestamp"].replace("Z", "").replace(" ", "T")
                if "." in ts_str:
                    ts = datetime.fromisoformat(ts_str.split(".")[0])
                else:
                    ts = datetime.fromisoformat(ts_str)
            except Exception:
                ts = None

        return LogEntry(
            timestamp=ts,
            level=level_str,
            component=data.get("component") or "general",
            message=data.get("message") or line_clean,
            raw=line_clean,
        )

    @staticmethod
    def _calculate_distribution_entropy(counts: Dict[str, int]) -> float:
        """Calculate Shannon entropy over categories."""
        total = sum(counts.values())
        if total <= 1:
            return 0.0
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 4)

    def analyze_logs(self, log_lines: List[str]) -> AnomalyReport:
        """Analyze a list of raw log lines and compute anomaly metrics."""
        if not log_lines:
            return AnomalyReport(
                total_lines=0,
                error_count=0,
                warning_count=0,
                anomaly_score=0.0,
                is_anomaly=False,
                burst_detected=False,
                unique_error_types=0,
                reasons=["No log entries to analyze"],
                recommendations=["Ensure log collector is sending active stream"],
            )

        entries = [self.parse_line(line) for line in log_lines if line.strip()]
        total_lines = len(entries)
        if total_lines == 0:
            return AnomalyReport(
                total_lines=0,
                error_count=0,
                warning_count=0,
                anomaly_score=0.0,
                is_anomaly=False,
                burst_detected=False,
                unique_error_types=0,
            )

        error_entries = [e for e in entries if e.level in ("EMERG", "ALERT", "CRIT", "ERROR")]
        warn_entries = [e for e in entries if e.level in ("WARN", "WARNING")]

        error_ratio = len(error_entries) / total_lines
        warn_ratio = len(warn_entries) / total_lines

        # Cluster error messages to identify distinct failure signatures
        error_signatures: Dict[str, int] = {}
        for err in error_entries:
            # Normalize message by removing numbers and hex addresses
            norm_msg = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", err.message)
            norm_msg = re.sub(r"\d+", "<NUM>", norm_msg).strip()
            error_signatures[norm_msg] = error_signatures.get(norm_msg, 0) + 1

        # Check for error burst (consecutive error sequence >= 5)
        burst_detected = False
        consecutive_errors = 0
        max_consecutive_errors = 0
        for e in entries:
            if e.level in ("EMERG", "ALERT", "CRIT", "ERROR"):
                consecutive_errors += 1
                if consecutive_errors > max_consecutive_errors:
                    max_consecutive_errors = consecutive_errors
            else:
                consecutive_errors = 0
        if max_consecutive_errors >= 5:
            burst_detected = True

        # Calculate heuristic risk score
        base_score = (error_ratio * 0.6) + (warn_ratio * 0.15)
        if burst_detected:
            base_score += 0.25

        # Critical error weighting
        has_critical = any(e.level in ("EMERG", "ALERT", "CRIT") for e in entries)
        if has_critical:
            base_score += 0.2

        final_score = min(1.0, round(base_score, 4))
        is_anomaly = final_score >= self.anomaly_threshold

        reasons: List[str] = []
        recommendations: List[str] = []

        if error_ratio > 0.15:
            reasons.append(f"High error density: {round(error_ratio * 100, 1)}% of logs are errors")
        if burst_detected:
            reasons.append(f"Error burst detected with {max_consecutive_errors} consecutive failures")
            recommendations.append("Investigate upstream dependency failure or network cascade")
        if has_critical:
            reasons.append("Critical severity level entries (CRIT/ALERT/EMERG) detected")
            recommendations.append("Trigger incident response on-call rotation")
        if len(error_signatures) > 3:
            reasons.append(f"Multiple diverse failure signatures observed ({len(error_signatures)} unique)")

        if not is_anomaly:
            reasons.append("Log stream behavior is within nominal thresholds")
            recommendations.append("Continue standard telemetry collection")

        return AnomalyReport(
            total_lines=total_lines,
            error_count=len(error_entries),
            warning_count=len(warn_entries),
            anomaly_score=final_score,
            is_anomaly=is_anomaly,
            burst_detected=burst_detected,
            unique_error_types=len(error_signatures),
            reasons=reasons,
            recommendations=recommendations,
        )
