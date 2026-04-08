#!/bin/bash
# Pashtelka pipeline runner — called by cron hourly during publishing hours.
#
# Cron: 0 8-21 * * * bash ~/workspace/projects/pashtelka-faion-net/scripts/run-pipeline.sh
#
# Runs one pipeline iteration per invocation (one article).
# State tracking prevents duplicate slots.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="/tmp/pashtelka-pipeline.lock"
LOG_DIR="$PROJECT_DIR/state/logs"

mkdir -p "$LOG_DIR"

# Prevent concurrent runs
if [ -f "$LOCK" ]; then
    PID=$(cat "$LOCK" 2>/dev/null || echo "")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Pipeline already running (PID $PID)" >> "$LOG_DIR/cron.log"
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

echo "$(date '+%Y-%m-%d %H:%M:%S') Pipeline run started" >> "$LOG_DIR/cron.log"

python3 -m pipeline -v >> "$LOG_DIR/cron.log" 2>&1
EXIT_CODE=$?

echo "$(date '+%Y-%m-%d %H:%M:%S') Pipeline exit: $EXIT_CODE" >> "$LOG_DIR/cron.log"
echo "---" >> "$LOG_DIR/cron.log"
