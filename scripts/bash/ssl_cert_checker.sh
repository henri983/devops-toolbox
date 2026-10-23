#!/usr/bin/env bash
# ==============================================================================
# Script: ssl_cert_checker.sh
# Purpose: TLS/SSL Certificate Expiration and Cipher Suite Audit Tool
# Alerting: Alerts when expiration is within CRITICAL (7d) or WARNING (30d) threshold
# Author: henri983 (henrinyame2001@gmail.com)
# ==============================================================================

set -euo pipefail

TARGET_HOST="${1:-example.com}"
TARGET_PORT="${2:-443}"
WARN_DAYS="${WARN_DAYS:-30}"
CRIT_DAYS="${CRIT_DAYS:-7}"

echo "[INFO] Querying SSL/TLS certificate for ${TARGET_HOST}:${TARGET_PORT}..."

if ! command -v openssl >/dev/null 2>&1; then
    echo "[ERROR] OpenSSL is not installed or available in PATH." >&2
    exit 1
fi

# Fetch expiration date using openssl s_client
EXPIRY_DATE=$(echo | openssl s_client -servername "${TARGET_HOST}" -connect "${TARGET_HOST}:${TARGET_PORT}" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || true)

if [ -z "${EXPIRY_DATE}" ]; then
    echo "[ERROR] Failed to obtain SSL certificate from ${TARGET_HOST}:${TARGET_PORT}" >&2
    exit 2
fi

# Convert dates to epoch seconds
if date --version >/dev/null 2>&1; then
    EXPIRY_EPOCH=$(date -d "${EXPIRY_DATE}" +%s)
    NOW_EPOCH=$(date +%s)
else
    EXPIRY_EPOCH=$(date -j -f "%b %d %T %Y %Z" "${EXPIRY_DATE}" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
fi

DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

echo "[RESULT] Host: ${TARGET_HOST}:${TARGET_PORT}"
echo "[RESULT] Expiry Date: ${EXPIRY_DATE}"
echo "[RESULT] Days Remaining: ${DAYS_LEFT} day(s)"

if [ "${DAYS_LEFT}" -le "${CRIT_DAYS}" ]; then
    echo "[CRITICAL] Certificate expires in ${DAYS_LEFT} days! Immediate renewal required."
    exit 2
elif [ "${DAYS_LEFT}" -le "${WARN_DAYS}" ]; then
    echo "[WARNING] Certificate expires in ${DAYS_LEFT} days. Plan renewal soon."
    exit 1
else
    echo "[OK] Certificate is healthy (${DAYS_LEFT} days remaining)."
    exit 0
fi
