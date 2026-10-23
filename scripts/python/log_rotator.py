"""Log Rotator - Production log compression, rotation, and retention lifecycle manager.

Author: henri983 (henrinyame2001@gmail.com)
Part of DevOps Toolbox Foundations
"""

from __future__ import annotations

import gzip
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class RotationAction:
    file_path: str
    action_type: str  # "compressed", "rotated", "purged"
    original_size_bytes: int
    compressed_size_bytes: int


@dataclass
class RotationSummary:
    files_processed: int
    total_bytes_saved: int
    actions: List[RotationAction]


class LogRotator:
    """Manages log file compression, file naming rotation, and retention purging."""

    def __init__(
        self,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10 MB default
        retention_days: int = 14,
        max_backups: int = 5,
    ) -> None:
        self.max_size_bytes = max_size_bytes
        self.retention_days = retention_days
        self.max_backups = max_backups

    def compress_file(self, target_file: Path) -> RotationAction:
        """Compress a single log file using gzip and remove original."""
        orig_size = target_file.stat().st_size
        gz_path = target_file.with_name(f"{target_file.name}.1.gz")

        # Shift existing .N.gz archives up to max_backups
        for i in range(self.max_backups - 1, 0, -1):
            older = target_file.with_name(f"{target_file.name}.{i}.gz")
            newer = target_file.with_name(f"{target_file.name}.{i + 1}.gz")
            if older.exists():
                if i + 1 > self.max_backups:
                    older.unlink()
                else:
                    older.rename(newer)

        with target_file.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        # Truncate original log file to 0 size so services can keep open descriptor
        with target_file.open("w") as f_truncate:
            f_truncate.truncate(0)

        compressed_size = gz_path.stat().st_size
        return RotationAction(
            file_path=str(target_file),
            action_type="compressed",
            original_size_bytes=orig_size,
            compressed_size_bytes=compressed_size,
        )

    def purge_expired_archives(self, directory: Path) -> List[RotationAction]:
        """Purge rotated .gz archives older than retention_days."""
        purged: List[RotationAction] = []
        now = time.time()
        retention_seconds = self.retention_days * 86400

        for gz_file in directory.glob("*.gz"):
            file_age = now - gz_file.stat().st_mtime
            if file_age > retention_seconds:
                size = gz_file.stat().st_size
                gz_file.unlink()
                purged.append(
                    RotationAction(
                        file_path=str(gz_file),
                        action_type="purged",
                        original_size_bytes=size,
                        compressed_size_bytes=0,
                    )
                )
        return purged

    def process_directory(self, directory: Path) -> RotationSummary:
        """Scan directory and compress files exceeding size limit, then purge expired."""
        actions: List[RotationAction] = []

        if not directory.exists() or not directory.is_dir():
            return RotationSummary(files_processed=0, total_bytes_saved=0, actions=[])

        # Evaluate active log files (*.log)
        for log_file in directory.glob("*.log"):
            if log_file.is_file() and log_file.stat().st_size >= self.max_size_bytes:
                act = self.compress_file(log_file)
                actions.append(act)

        # Evaluate expired archives
        purged = self.purge_expired_archives(directory)
        actions.extend(purged)

        bytes_saved = sum(
            max(0, a.original_size_bytes - a.compressed_size_bytes)
            for a in actions
            if a.action_type == "compressed"
        )

        return RotationSummary(
            files_processed=len(actions),
            total_bytes_saved=bytes_saved,
            actions=actions,
        )
