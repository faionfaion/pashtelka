#!/bin/bash
# Pashtelka pipeline runner — called by cron.
#
# Cron schedule (UTC — server timezone):
#   0 6 * * *            bash ~/workspace/projects/pashtelka-faion-net/scripts/run-pipeline.sh generate
#   5 8,11,14,17 * * *   bash ~/workspace/projects/pashtelka-faion-net/scripts/run-pipeline.sh publish
#   5 19 * * *           bash ~/workspace/projects/pashtelka-faion-net/scripts/run-pipeline.sh digest
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
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:$PATH"
export HOME="${HOME:-/home/nero}"
[ -f "$HOME/workspace/.env" ] && source "$HOME/workspace/.env"

# Activate shared media venv if present (faion-net runtime). On hosts without
# this venv (e.g. nero-prod), fall through to system python3.
if [ -f "$HOME/.venv-media/bin/activate" ] && [ -z "${VIRTUAL_ENV:-}" ]; then
    # shellcheck disable=SC1091
    source "$HOME/.venv-media/bin/activate"
fi

# Pull latest changes (admin edits, prompt updates)
git pull --ff-only origin master >> "$LOG_DIR/cron.log" 2>&1 || true

echo "$(date '+%Y-%m-%d %H:%M:%S') Pipeline $MODE started" >> "$LOG_DIR/cron.log"

python3 -m pipeline "$MODE" -v >> "$LOG_DIR/cron.log" 2>&1
EXIT_CODE=$?

echo "$(date '+%Y-%m-%d %H:%M:%S') Pipeline $MODE exit: $EXIT_CODE" >> "$LOG_DIR/cron.log"

# After a successful generate, drain today's queue to TG immediately.
# Each `publish` call posts ONE article; loop until there is nothing
# left so the channel is current as soon as generate finishes.
if [ "$MODE" = "generate" ] && [ "$EXIT_CODE" -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') Draining publish queue" >> "$LOG_DIR/cron.log"
    for _ in $(seq 1 20); do
        python3 -m pipeline publish -v >> "$LOG_DIR/cron.log" 2>&1
        PUB_RC=$?
        if [ "$PUB_RC" -ne 0 ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') Publish exit: $PUB_RC (stopping)" >> "$LOG_DIR/cron.log"
            break
        fi
        if tail -5 "$LOG_DIR/cron.log" | grep -q "Nothing to publish"; then
            break
        fi
        sleep 60
    done
fi

echo "---" >> "$LOG_DIR/cron.log"
