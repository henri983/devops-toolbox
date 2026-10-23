"""Unit tests for log_rotator.py."""

from __future__ import annotations

import gzip
from pathlib import Path

from scripts.python.log_rotator import LogRotator


def test_compress_large_log_file(temp_dir: Path) -> None:
    rotator = LogRotator(max_size_bytes=500, retention_days=7, max_backups=2)
    log_file = temp_dir / "app.log"
    # Write ~1 KB of log text
    log_file.write_text("2026-10-23 20:00:00 [INFO] test event log message line\n" * 20)

    action = rotator.compress_file(log_file)
    assert action.action_type == "compressed"
    assert action.original_size_bytes > 500

    gz_file = temp_dir / "app.log.1.gz"
    assert gz_file.exists()

    # Verify content in gzip
    with gzip.open(gz_file, "rt") as f:
        content = f.read()
    assert "test event log message" in content

    # Original file is truncated to 0 bytes
    assert log_file.stat().st_size == 0


def test_process_directory_rotates_and_ignores_small(temp_dir: Path) -> None:
    rotator = LogRotator(max_size_bytes=1000, retention_days=7)
    small_log = temp_dir / "small.log"
    small_log.write_text("tiny log entry\n")

    big_log = temp_dir / "big.log"
    big_log.write_text("big log payload line\n" * 100)

    summary = rotator.process_directory(temp_dir)
    assert summary.files_processed >= 1
    assert (temp_dir / "big.log.1.gz").exists()
    assert not (temp_dir / "small.log.1.gz").exists()
