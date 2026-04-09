#!/bin/bash
# Pashtelka pipeline runner — called by cron.
#
# Cron schedule (Lisbon time = UTC in winter, UTC+1 in summer):
#   0 7 * * *          bash ~/workspace/projects/pashtelka-faion-net/scripts/run-pipeline.sh generate
#   5 9,12,15,18 * * * bash ~/workspace/projects/pashtelka-faion-net/scripts/run-pipeline.sh publish
#   5 20 * * *         bash ~/workspace/projects/pashtelka-faion-net/scripts/run-pipeline.sh digest
#
# Modes:
#   generate — morning batch: editorial plan + all articles + deploy site
#   publish  — mechanical: pick pre-generated article, send to TG
#   digest   — evening digest to TG

set -euo pipefail

MODE="${1:-generate}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="/tmp/pashtelka-${MODE}.lock"
LOG_DIR="$PROJECT_DIR/state/logs"

mkdir -p "$LOG_DIR"

# Prevent concurrent runs of same mode
if [ -f "$LOCK" ]; then
    PID=$(cat "$LOCK" 2>/dev/null || echo "")
    if kill -0 "$PID" 2>/dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') Pipeline $MODE already running (PID $PID)" >> "$LOG_DIR/cron.log"
        exit 0
    fi
    rm -f "$LOCK"
fi
echo $$ > "$LOCK"
trap "rm -f $LOCK" EXIT

cd "$PROJECT_DIR"

# Load environment
export PATH="/usr/local/bin:/usr/bin:$PATH"
export HOME="${HOME:-/home/nero}"
[ -f "$HOME/workspace/.env" ] && source "$HOME/workspace/.env"

# Pull latest changes (admin edits, prompt updates)
git pull --ff-only origin master >> "$LOG_DIR/cron.log" 2>&1 || true

echo "$(date '+%Y-%m-%d %H:%M:%S') Pipeline $MODE started" >> "$LOG_DIR/cron.log"

python3 -m pipeline "$MODE" -v >> "$LOG_DIR/cron.log" 2>&1
EXIT_CODE=$?

echo "$(date '+%Y-%m-%d %H:%M:%S') Pipeline $MODE exit: $EXIT_CODE" >> "$LOG_DIR/cron.log"
echo "---" >> "$LOG_DIR/cron.log"
