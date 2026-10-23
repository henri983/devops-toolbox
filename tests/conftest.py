"""Pytest configuration and common fixtures for DevOps Toolbox."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from scripts.python.cloud_cost_optimizer import CloudCostOptimizer
from scripts.python.log_rotator import LogRotator
from scripts.python.secret_scanner import SecretScanner
from src.ai.drift_analyzer import DriftAnalyzer
from src.ai.log_anomaly_detector import LogAnomalyDetector


@pytest.fixture
def secret_scanner() -> SecretScanner:
    return SecretScanner(entropy_threshold=4.0)


@pytest.fixture
def cost_optimizer() -> CloudCostOptimizer:
    return CloudCostOptimizer(idle_cpu_threshold=5.0)


@pytest.fixture
def log_rotator() -> LogRotator:
    return LogRotator(max_size_bytes=1024, retention_days=7, max_backups=3)


@pytest.fixture
def log_anomaly_detector() -> LogAnomalyDetector:
    return LogAnomalyDetector(anomaly_threshold=0.65)


@pytest.fixture
def drift_analyzer() -> DriftAnalyzer:
    return DriftAnalyzer(drift_threshold=0.20)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)
