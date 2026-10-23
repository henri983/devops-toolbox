#!/usr/bin/env bash
# ==============================================================================
# Script: system_health_audit.sh
# Purpose: Comprehensive system health check (CPU, RAM, Disk, Port, Zombies)
# Output: Formatted text or JSON report for observability pipelines
# Author: henri983 (henrinyame2001@gmail.com)
# ==============================================================================

set -euo pipefail

FORMAT="${1:---text}"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
HOSTNAME="$(hostname)"

# Resource metrics collection
UPTIME_SEC=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo 0)
LOAD_1M=$(awk '{print $1}' /proc/loadavg 2>/dev/null || echo 0.0)

# Memory metrics (kB to MB conversion)
MEM_TOTAL_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 1)
MEM_AVAIL_KB=$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
MEM_USED_KB=$(( MEM_TOTAL_KB - MEM_AVAIL_KB ))
MEM_USED_PCT=$(( (MEM_USED_KB * 100) / (MEM_TOTAL_KB > 0 ? MEM_TOTAL_KB : 1) ))

# Disk metrics for root mount
DISK_USED_PCT=$(df / 2>/dev/null | awk 'NR==2 {gsub("%","",$5); print $5}' || echo 0)

# Zombie process counter
ZOMBIE_COUNT=$(ps -eo stat 2>/dev/null | grep -c 'Z' || echo 0)

# Health classification
HEALTH_STATUS="HEALTHY"
if [ "${DISK_USED_PCT}" -gt 90 ] || [ "${MEM_USED_PCT}" -gt 90 ]; then
    HEALTH_STATUS="CRITICAL"
elif [ "${DISK_USED_PCT}" -gt 80 ] || [ "${MEM_USED_PCT}" -gt 80 ] || [ "${ZOMBIE_COUNT}" -gt 0 ]; then
    HEALTH_STATUS="WARNING"
fi

if [ "${FORMAT}" = "--json" ]; then
    cat <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "hostname": "${HOSTNAME}",
  "status": "${HEALTH_STATUS}",
  "metrics": {
    "load_1m": ${LOAD_1M},
    "memory_used_percent": ${MEM_USED_PCT},
    "disk_used_percent": ${DISK_USED_PCT},
    "zombie_processes": ${ZOMBIE_COUNT},
    "uptime_seconds": ${UPTIME_SEC}
  }
}
EOF
else
    echo "=========================================================="
    echo " System Health Audit Report: ${HOSTNAME}"
    echo " Status: [${HEALTH_STATUS}] | Timestamp: ${TIMESTAMP}"
    echo "=========================================================="
    echo " - Load Average (1m):       ${LOAD_1M}"
    echo " - RAM Usage:               ${MEM_USED_PCT}%"
    echo " - Disk Usage (/):          ${DISK_USED_PCT}%"
    echo " - Zombie Processes:        ${ZOMBIE_COUNT}"
    echo " - System Uptime:           ${UPTIME_SEC}s"
    echo "=========================================================="
fi
