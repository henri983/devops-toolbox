"""Tests for AI SysAdmin Copilot - Log Anomaly Detector."""

from __future__ import annotations

from src.ai.log_anomaly_detector import LogAnomalyDetector


def test_parse_log_line_iso(log_anomaly_detector: LogAnomalyDetector) -> None:
    line = "2026-10-23T20:15:00 [ERROR] [auth-service]: Failed password for invalid user admin from 192.168.1.100"
    entry = log_anomaly_detector.parse_line(line)
    assert entry.level == "ERROR"
    assert entry.component == "auth-service"
    assert "Failed password" in entry.message


def test_nominal_log_stream_nominal_score(log_anomaly_detector: LogAnomalyDetector) -> None:
    lines = [
        "2026-10-23T20:00:01 [INFO] [web]: GET /health 200 OK",
        "2026-10-23T20:00:02 [INFO] [web]: GET /metrics 200 OK",
        "2026-10-23T20:00:03 [INFO] [worker]: Processed job #1042 successfully",
        "2026-10-23T20:00:04 [DEBUG] [cache]: Cache hit ratio 98.4%",
        "2026-10-23T20:00:05 [INFO] [web]: GET /api/v1/status 200 OK",
    ]
    report = log_anomaly_detector.analyze_logs(lines)
    assert report.total_lines == 5
    assert report.error_count == 0
    assert report.is_anomaly is False
    assert report.anomaly_score < 0.3


def test_high_error_density_triggers_alert(log_anomaly_detector: LogAnomalyDetector) -> None:
    lines = [
        "2026-10-23T20:00:01 [ERROR] [database]: Connection refused to postgres:5432",
        "2026-10-23T20:00:02 [ERROR] [database]: Connection refused to postgres:5432",
        "2026-10-23T20:00:03 [CRITICAL] [auth]: Unable to fetch session from DB",
        "2026-10-23T20:00:04 [ERROR] [gateway]: 500 Internal Server Error",
    ]
    report = log_anomaly_detector.analyze_logs(lines)
    assert report.error_count == 4
    assert report.anomaly_score >= 0.65
    assert report.is_anomaly is True


def test_burst_detection(log_anomaly_detector: LogAnomalyDetector) -> None:
    lines = [f"2026-10-23T20:00:{i:02d} [ERROR] [service]: Panic timeout exception {i}" for i in range(6)]
    report = log_anomaly_detector.analyze_logs(lines)
    assert report.burst_detected is True
    assert report.is_anomaly is True


def test_empty_logs_handling(log_anomaly_detector: LogAnomalyDetector) -> None:
    report = log_anomaly_detector.analyze_logs([])
    assert report.total_lines == 0
    assert report.is_anomaly is False
