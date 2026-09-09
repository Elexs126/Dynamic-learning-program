#!/bin/bash
# Antigravity IDE launcher with automatic conversation index repair.
# Runs the repair script before starting the IDE.

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
LOG_FILE="$HOME/.gemini/antigravity-ide/repair.log"

# Search for repair script across possible locations
REPAIR_SCRIPT=""
CANDIDATES=(
    "$SCRIPT_DIR/agy-repair-conversations.py"
    "$HOME/.local/share/antigravity-ide/scripts/agy-repair-conversations.py"
    "$HOME/Dynamic-learning-program/系统文件/IDE脚本/agy-repair-conversations.py"
)

for cand in "${CANDIDATES[@]}"; do
    if [ -f "$cand" ]; then
        REPAIR_SCRIPT="$cand"
        break
    fi
done

if [ -n "$REPAIR_SCRIPT" ]; then
    mkdir -p "$(dirname "$LOG_FILE")"
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "=== [$TIMESTAMP] Antigravity Launch Check ===" >> "$LOG_FILE"
    
    # Run repair and capture output to log as well as stdout if running interactively
    if [ -t 1 ]; then
        python3 "$REPAIR_SCRIPT" 2>&1 | tee -a "$LOG_FILE" | head -20
    else
        python3 "$REPAIR_SCRIPT" >> "$LOG_FILE" 2>&1
    fi
    echo "----------------------------------------" >> "$LOG_FILE"
fi

exec /home/elexs/.local/opt/antigravity-ide/bin/antigravity-ide "$@"
