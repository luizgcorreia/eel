#!/usr/bin/env bash

# Screen Manager for Resilient Google Drive Backup
# Usage: ./scripts/run_backup_screen.sh [start|status|stop|attach|logs]

SESSION_NAME="erdos_gdrive_backup"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/gdrive_backup.sh"
LOG_FILE="$(dirname "$SCRIPT_DIR")/backup_rclone.log"

chmod +x "${BACKUP_SCRIPT}"

start_backup() {
    if screen -list | grep -q "\.${SESSION_NAME}"; then
        echo "Backup screen session '${SESSION_NAME}' is ALREADY RUNNING."
        echo "To view status, run: ./scripts/run_backup_screen.sh status"
        echo "To attach, run: screen -r ${SESSION_NAME}"
    else
        echo "Starting backup in detached screen session '${SESSION_NAME}'..."
        screen -dmS "${SESSION_NAME}" bash -c "cd '$(dirname "$SCRIPT_DIR")' && '${BACKUP_SCRIPT}'"
        sleep 1
        if screen -list | grep -q "\.${SESSION_NAME}"; then
            echo "SUCCESS: Screen session '${SESSION_NAME}' started."
            echo "Log output is being saved to: ${LOG_FILE}"
        else
            echo "ERROR: Failed to start screen session '${SESSION_NAME}'."
        fi
    fi
}

status_backup() {
    if screen -list | grep -q "\.${SESSION_NAME}"; then
        echo "Status: RUNNING (screen session '${SESSION_NAME}')"
        if [ -f "${LOG_FILE}" ]; then
            echo "--- Recent Log Output ---"
            tail -n 15 "${LOG_FILE}"
        fi
    else
        echo "Status: NOT RUNNING"
        if [ -f "${LOG_FILE}" ]; then
            echo "--- Last Log Output ---"
            tail -n 15 "${LOG_FILE}"
        fi
    fi
}

stop_backup() {
    if screen -list | grep -q "\.${SESSION_NAME}"; then
        echo "Stopping screen session '${SESSION_NAME}'..."
        screen -X -S "${SESSION_NAME}" quit
        echo "Stopped."
    else
        echo "Session '${SESSION_NAME}' is not running."
    fi
}

attach_backup() {
    if screen -list | grep -q "\.${SESSION_NAME}"; then
        screen -r "${SESSION_NAME}"
    else
        echo "Session '${SESSION_NAME}' is not running."
    fi
}

logs_backup() {
    if [ -f "${LOG_FILE}" ]; then
        tail -f "${LOG_FILE}"
    else
        echo "Log file '${LOG_FILE}' does not exist yet."
    fi
}

case "$1" in
    start)
        start_backup
        ;;
    status)
        status_backup
        ;;
    stop)
        stop_backup
        ;;
    attach)
        attach_backup
        ;;
    logs)
        logs_backup
        ;;
    *)
        start_backup
        ;;
esac
