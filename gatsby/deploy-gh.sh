#!/bin/bash
set -euo pipefail

# Deploy pashtelka.faion.net (pastelka.news)
# Push to GitHub → SSH to faion-net → pull + build + deploy

REPO_URL="git@github.com:faionfaion/pashtelka.git"
BRANCH="master"
REMOTE_DIR="/home/faion/pashtelka"
WEBROOT="/var/www/pashtelka.faion.net"
SITE="pashtelka.faion.net"
SSH="ssh faion@46.225.58.119 -p 22022"

cd "$(dirname "$0")/.."

echo "==> Deploying $SITE"

# 1. Push to GitHub
echo "  Pushing to GitHub..."
git add -A
git diff --cached --quiet 2>/dev/null || git commit -m "content: auto-publish $(date +%Y-%m-%d)"
git push origin "$BRANCH" 2>/dev/null || git push -u origin "$BRANCH"

# 2. Remote: pull, build, deploy
$SSH bash -s -- "$REPO_URL" "$BRANCH" "$REMOTE_DIR" "$WEBROOT" "$SITE" <<'REMOTE'
set -euo pipefail
REPO_URL="$1"; BRANCH="$2"; REMOTE_DIR="$3"; WEBROOT="$4"; SITE="$5"

echo "  [remote] Syncing repo..."
if [ -d "$REMOTE_DIR/.git" ]; then
    cd "$REMOTE_DIR"
    git remote set-url origin "$REPO_URL" 2>/dev/null || true
    git fetch origin "$BRANCH" --quiet
    git reset --hard "origin/$BRANCH" --quiet
else
    git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$REMOTE_DIR" --quiet
    cd "$REMOTE_DIR"
fi
echo "  [remote] At $(git rev-parse --short HEAD)"

echo "  [remote] Installing deps..."
cd "$REMOTE_DIR/gatsby"
npm ci --silent 2>/dev/null || npm install --silent

echo "  [remote] Building..."
npx gatsby build

echo "  [remote] Deploying to $WEBROOT..."
mkdir -p "$WEBROOT"
rsync -a --delete public/ "$WEBROOT/"

sudo nginx -t && sudo systemctl reload nginx
echo "  [remote] Done."
REMOTE

echo "==> Deployed https://pastelka.news/"
