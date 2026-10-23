"""Unit tests for secret_scanner.py."""

from __future__ import annotations

from pathlib import Path

from scripts.python.secret_scanner import SecretScanner


def test_calculate_shannon_entropy(secret_scanner: SecretScanner) -> None:
    # Monotonous repetitive string has very low entropy
    low_ent = secret_scanner.calculate_shannon_entropy("aaaaaaaaaaaa")
    assert low_ent == 0.0

    # Random mixed-character string has higher entropy (> 4.0)
    high_ent = secret_scanner.calculate_shannon_entropy("X9#mK$2pL!9zQ@1vW&4rB*7y")
    assert high_ent > 4.0


def test_mask_secret(secret_scanner: SecretScanner) -> None:
    assert secret_scanner.mask_secret("AKIAIOSFODNN7EXAMPLE") == "AK...LE"
    assert secret_scanner.mask_secret("123") == "***"


def test_detect_aws_credentials(secret_scanner: SecretScanner) -> None:
    text = "aws_access_key = 'AKIA1234567890ABCDEF'\naws_secret = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"
    findings = secret_scanner.scan_content(text)
    types = [f.secret_type for f in findings]
    assert "AWS Access Key" in types


def test_detect_private_key_header(secret_scanner: SecretScanner) -> None:
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----"
    findings = secret_scanner.scan_content(text)
    assert any("Private Key" in f.secret_type for f in findings)


def test_detect_jwt_token(secret_scanner: SecretScanner) -> None:
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozG4B_EXAMPLE"
    findings = secret_scanner.scan_content(text)
    assert any("JSON Web Token" in f.secret_type for f in findings)


def test_clean_file_yields_no_findings(secret_scanner: SecretScanner, temp_dir: Path) -> None:
    clean_file = temp_dir / "clean_config.py"
    clean_file.write_text("DEBUG = True\nPORT = 8080\nAPP_NAME = 'DevOpsToolbox'\n")
    findings = secret_scanner.scan_file(clean_file)
    assert len(findings) == 0


def test_scan_directory_recursive(secret_scanner: SecretScanner, temp_dir: Path) -> None:
    sub = temp_dir / "subdir"
    sub.mkdir()
    secret_file = sub / "credentials.txt"
    secret_file.write_text("token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'\n")
    findings = secret_scanner.scan_directory(temp_dir)
    assert len(findings) >= 1
    assert any("GitHub Token" in f.secret_type for f in findings)
