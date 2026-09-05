#!/bin/bash
# Antigravity IDE launcher with automatic conversation index repair.
# Runs the repair script before starting the IDE.

REPAIR_SCRIPT="$HOME/Dynamic-learning-program/系统文件/脚本/agy-repair-conversations.py"

if [ -f "$REPAIR_SCRIPT" ]; then
    python3 "$REPAIR_SCRIPT" 2>&1 | head -20
    echo "---"
fi

exec /home/elexs/.local/opt/antigravity-ide/bin/antigravity-ide "$@"
