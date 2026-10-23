#!/usr/bin/env bash
# ==============================================================================
# Script: docker_prune_safe.sh
# Purpose: Safe Docker cleanup tool with dry-run support and volume preservation
# Author: henri983 (henrinyame2001@gmail.com)
# ==============================================================================

set -euo pipefail

DRY_RUN="${1:---dry-run}"
MAX_LOG_HOURS="${MAX_LOG_HOURS:-168}" # 7 days

echo "[INFO] Running Docker Safe Cleanup Tool (Mode: ${DRY_RUN})"

if ! command -v docker >/dev/null 2>&1; then
    echo "[WARN] Docker engine binary not located. Skipping cleanup."
    exit 0
fi

if [ "${DRY_RUN}" = "--dry-run" ]; then
    echo "[DRY-RUN] Stopped containers that would be removed:"
    docker ps -a --filter "status=exited" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}" || true
    echo "[DRY-RUN] Dangling images that would be reclaimed:"
    docker images -f "dangling=true" --format "table {{.ID}}\t{{.Repository}}\t{{.Tag}}\t{{.Size}}" || true
    echo "[DRY-RUN] Unused bridge networks:"
    docker network ls --filter "driver=bridge" --filter "type=custom" || true
    echo "[INFO] Re-run with '--force' to execute pruning."
elif [ "${DRY_RUN}" = "--force" ]; then
    echo "[ACTION] Pruning stopped containers..."
    docker container prune -f
    echo "[ACTION] Pruning dangling images..."
    docker image prune -f
    echo "[ACTION] Pruning unused custom networks..."
    docker network prune -f
    echo "[ACTION] Pruning build cache older than ${MAX_LOG_HOURS}h..."
    docker builder prune -f --filter "until=${MAX_LOG_HOURS}h" || true
    echo "[SUCCESS] Safe Docker cleanup completed. Named volumes were preserved."
else
    echo "[ERROR] Unknown option: ${DRY_RUN}. Use '--dry-run' or '--force'."
    exit 1
fi
