"""Secret Scanner - Static entropy and regex-based credential leak detection.

Author: henri983 (henrinyame2001@gmail.com)
Part of DevOps Toolbox Foundations
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SecretFinding:
    file_path: str
    line_number: int
    secret_type: str
    sample_masked: str
    entropy: float


class SecretScanner:
    """Scanner that detects credentials, keys, and high-entropy secrets in text and repositories."""

    REGEX_PATTERNS: Dict[str, re.Pattern[str]] = {
        "AWS Access Key": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "AWS Secret Key": re.compile(r"\b([a-zA-Z0-9+/]{40})\b"),
        "GitHub Token": re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b"),
        "Private Key Header": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "JSON Web Token": re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]+\b"),
        "Generic API Key / Secret": re.compile(r"""(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['"]([a-zA-Z0-9_\-\.]{16,})['"]"""),
    }

    def __init__(self, entropy_threshold: float = 4.2) -> None:
        self.entropy_threshold = entropy_threshold

    @staticmethod
    def calculate_shannon_entropy(data: str) -> float:
        """Calculate the Shannon entropy of a given string.

        Higher entropy (> 4.0) often indicates cryptographic keys or random tokens.
        """
        if not data:
            return 0.0
        entropy = 0.0
        length = len(data)
        frequencies: Dict[str, int] = {}
        for char in data:
            frequencies[char] = frequencies.get(char, 0) + 1
        for count in frequencies.values():
            prob = count / length
            entropy -= prob * math.log2(prob)
        return round(entropy, 4)

    @staticmethod
    def mask_secret(secret: str) -> str:
        """Mask secrets leaving only first 2 and last 2 characters visible."""
        if len(secret) <= 6:
            return "***"
        return f"{secret[:2]}...{secret[-2:]}"

    def scan_content(self, content: str, file_path: str = "<memory>") -> List[SecretFinding]:
        """Scan a multiline text content for leaked secrets."""
        findings: List[SecretFinding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            # Check pattern matches
            for secret_type, pattern in self.REGEX_PATTERNS.items():
                matches = pattern.findall(line)
                for match in matches:
                    secret_val = match if isinstance(match, str) else match[-1]
                    entropy = self.calculate_shannon_entropy(secret_val)
                    findings.append(
                        SecretFinding(
                            file_path=file_path,
                            line_number=idx,
                            secret_type=secret_type,
                            sample_masked=self.mask_secret(secret_val),
                            entropy=entropy,
                        )
                    )

            # Check general words for raw high entropy (potential un-flagged secrets)
            tokens = re.findall(r"\b[A-Za-z0-9+/=_-]{24,}\b", line)
            for token in tokens:
                ent = self.calculate_shannon_entropy(token)
                if ent >= self.entropy_threshold:
                    # Avoid duplicate if already caught by regex
                    if not any(f.line_number == idx and token in line for f in findings):
                        findings.append(
                            SecretFinding(
                                file_path=file_path,
                                line_number=idx,
                                secret_type="High Entropy String",
                                sample_masked=self.mask_secret(token),
                                entropy=ent,
                            )
                        )

        return findings

    def scan_file(self, file_path: Path) -> List[SecretFinding]:
        """Read and scan a file safely."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return self.scan_content(content, file_path=str(file_path))
        except Exception:
            return []

    def scan_directory(self, target_dir: Path, ignored_dirs: Optional[List[str]] = None) -> List[SecretFinding]:
        """Recursively scan a directory for leaked secrets."""
        if ignored_dirs is None:
            ignored_dirs = [".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"]

        all_findings: List[SecretFinding] = []
        for file in target_dir.rglob("*"):
            if file.is_file() and not any(part in file.parts for part in ignored_dirs):
                all_findings.extend(self.scan_file(file))
        return all_findings
