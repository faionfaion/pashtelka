#!/bin/bash
set -euo pipefail

# Deploy pashtelka.faion.net to Cloudflare Pages
#
# Usage: bash gatsby/deploy-gh.sh
#
# Requires: CLOUDFLARE_API_TOKEN set or available via OP

GATSBY_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$GATSBY_DIR")"

echo "==> Deploying pashtelka.faion.net (Cloudflare Pages)"

# 1. Build Gatsby
echo "  Building Gatsby site..."
cd "$GATSBY_DIR"
npx gatsby build --quiet 2>&1

# 2. Deploy to Cloudflare Pages
echo "  Deploying to Cloudflare Pages..."
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-cfut_GnhGHOEdw8QtfoSypAkgwmRQ5f2LtH6WZjcLfUaC74f10919}" \
CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-d2894a6bccc5fa09c135663909c52afa}" \
npx wrangler pages deploy public/ --project-name=pashtelka --branch=main --commit-dirty=true 2>&1

echo "==> Deployed: https://pashtelka.faion.net/"
