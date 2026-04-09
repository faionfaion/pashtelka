#!/bin/bash
set -euo pipefail
# Deploy pashtelka.faion.net — push to GitHub then deploy on server
cd "$(dirname "$0")/.."

echo "==> Pushing to GitHub..."
git add -A
git diff --cached --quiet 2>/dev/null || git commit -m "content: auto-publish $(date +%Y-%m-%d)"
git push origin master 2>/dev/null || git push -u origin master

echo "==> Deploying to faion-net..."
bash gatsby/deploy-server.sh
