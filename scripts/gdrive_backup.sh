#!/usr/bin/env bash

# Resilient Google Drive Backup Script for artifacts
# Works on erdos (or any Linux machine with bash and screen)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="${WORKSPACE_DIR}/artifacts"
LOG_FILE="${WORKSPACE_DIR}/backup_rclone.log"
RCLONE_CONFIG_DIR="${HOME}/.config/rclone"
RCLONE_CONFIG_FILE="${RCLONE_CONFIG_DIR}/rclone.conf"
REMOTE_FOLDER="gdrive:artifacts_backup"

# Step 1: Ensure rclone is available
if ! command -v rclone &> /dev/null; then
    if [ -f "${HOME}/.local/bin/rclone" ]; then
        export PATH="${HOME}/.local/bin:${PATH}"
    else
        echo "[$(date)] rclone binary not found. Downloading static rclone binary..." >> "${LOG_FILE}"
        mkdir -p "${HOME}/.local/bin"
        TMP_DIR="$(mktemp -d)"
        curl -sSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o "${TMP_DIR}/rclone.zip"
        unzip -q "${TMP_DIR}/rclone.zip" -d "${TMP_DIR}/"
        cp "${TMP_DIR}"/rclone-*-linux-amd64/rclone "${HOME}/.local/bin/"
        chmod +x "${HOME}/.local/bin/rclone"
        rm -rf "${TMP_DIR}"
        export PATH="${HOME}/.local/bin:${PATH}"
        echo "[$(date)] rclone installed to ${HOME}/.local/bin/rclone" >> "${LOG_FILE}"
    fi
fi

# Step 2: Ensure rclone.conf is configured with Google Drive OAuth token
mkdir -p "${RCLONE_CONFIG_DIR}"
if ! grep -q "\[gdrive\]" "${RCLONE_CONFIG_FILE}" 2>/dev/null; then
    if [ -n "${RCLONE_GDRIVE_TOKEN:-}" ]; then
        echo "[$(date)] Writing Google Drive rclone configuration from environment..." >> "${LOG_FILE}"
        cat << EOF >> "${RCLONE_CONFIG_FILE}"
[gdrive]
type = drive
scope = drive
token = ${RCLONE_GDRIVE_TOKEN}
EOF
    else
        echo "[$(date)] Note: rclone [gdrive] not configured. Please run 'rclone config' or set RCLONE_GDRIVE_TOKEN." >> "${LOG_FILE}"
    fi
fi

# Step 3: Verify source artifacts directory
if [ ! -d "${ARTIFACTS_DIR}" ]; then
    echo "[$(date)] Error: Artifacts directory '${ARTIFACTS_DIR}' does not exist!" >> "${LOG_FILE}"
    exit 1
fi

echo "=================================================" >> "${LOG_FILE}"
echo "[$(date)] Starting Resilient Artifacts Backup to Google Drive" >> "${LOG_FILE}"
echo "Source: ${ARTIFACTS_DIR}" >> "${LOG_FILE}"
echo "Destination: ${REMOTE_FOLDER}" >> "${LOG_FILE}"
echo "Log File: ${LOG_FILE}" >> "${LOG_FILE}"
echo "=================================================" >> "${LOG_FILE}"

# Step 4: Resilient Loop
MAX_RETRIES=1000
RETRY_COUNT=0
SLEEP_INTERVAL=10

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "[$(date)] Backup attempt #${RETRY_COUNT} starting..." >> "${LOG_FILE}"
    
    rclone copy "${ARTIFACTS_DIR}" "${REMOTE_FOLDER}" \
        --retries 50 \
        --low-level-retries 50 \
        --retries-sleep 10s \
        --transfers 4 \
        --checkers 8 \
        --update \
        --stats 30s \
        --stats-one-line \
        --verbose \
        >> "${LOG_FILE}" 2>&1 && EXIT_CODE=0 || EXIT_CODE=$?

    if [ ${EXIT_CODE} -eq 0 ]; then
        echo "[$(date)] SUCCESS: Backup completed successfully on attempt #${RETRY_COUNT}!" >> "${LOG_FILE}"
        break
    else
        echo "[$(date)] WARNING: rclone copy exited with code ${EXIT_CODE}. Retrying in ${SLEEP_INTERVAL}s..." >> "${LOG_FILE}"
        sleep ${SLEEP_INTERVAL}
    fi
done

echo "[$(date)] Backup process finished." >> "${LOG_FILE}"
