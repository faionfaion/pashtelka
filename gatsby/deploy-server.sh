#!/bin/bash
set -euo pipefail

# Deploy pashtelka.faion.net to faion-net server (like neromedia).
#
# 1. SSH into faion-net
# 2. Pull latest from GitHub
# 3. Build Gatsby on remote
# 4. Copy to nginx webroot
# 5. Setup nginx config if needed
#
# Prerequisites: source ~/bin/op_unlock.sh

REPO_URL="https://github.com/faionfaion/pashtelka.git"
BRANCH="master"
REMOTE_DIR="/home/faion/pashtelka"
WEBROOT="/var/www/pashtelka.faion.net"

echo "==> Deploying pashtelka.faion.net (GitHub → faion-net)"

# 1. Get SSH credentials
HOST=$(op item get "SSH faion-net" --vault="Faion Personal" --fields host --reveal 2>/dev/null)
PORT=$(op item get "SSH faion-net" --vault="Faion Personal" --fields port --reveal 2>/dev/null)
USER=$(op item get "SSH faion-net" --vault="Faion Personal" --fields user --reveal 2>/dev/null)
KEY=$(op item get "SSH faion-net" --vault="Faion Personal" --fields ssh_private_key 2>/dev/null | tr -d '"')

KEYFILE=$(mktemp)
trap "rm -f $KEYFILE" EXIT
printf '%s\n' "$KEY" > "$KEYFILE"
chmod 600 "$KEYFILE"

SSH_CMD="ssh -i $KEYFILE -p $PORT -o StrictHostKeyChecking=no"

# 2. Run deploy on remote
$SSH_CMD "$USER@$HOST" bash -s -- "$REPO_URL" "$BRANCH" "$REMOTE_DIR" "$WEBROOT" <<'REMOTE_SCRIPT'
set -euo pipefail

REPO_URL="$1"
BRANCH="$2"
REMOTE_DIR="$3"
WEBROOT="$4"

echo "  [remote] Pulling repo..."
if [ -d "$REMOTE_DIR/.git" ]; then
    cd "$REMOTE_DIR"
    git fetch origin
    git reset --hard "origin/$BRANCH"
else
    git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$REMOTE_DIR"
    cd "$REMOTE_DIR"
fi

echo "  [remote] Installing dependencies..."
cd gatsby
npm ci --production 2>/dev/null || npm install 2>/dev/null

echo "  [remote] Building Gatsby..."
npx gatsby build

echo "  [remote] Deploying to webroot..."
mkdir -p "$WEBROOT"
rsync -a --delete public/ "$WEBROOT/"

# Setup nginx if not exists
NGINX_CONF="/etc/nginx/sites-enabled/pashtelka.faion.net"
if [ ! -f "$NGINX_CONF" ]; then
    echo "  [remote] Creating nginx config..."
    cat > "$NGINX_CONF" <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name pashtelka.faion.net;

    root /var/www/pashtelka.faion.net;
    index index.html;

    location / {
        try_files $uri $uri/ $uri/index.html =404;
    }

    location /images/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header Referrer-Policy strict-origin-when-cross-origin;
}
NGINX
    nginx -t && systemctl reload nginx
    echo "  [remote] Nginx configured and reloaded"
fi

echo "  [remote] Done! Site: https://pashtelka.faion.net/"
REMOTE_SCRIPT

echo "==> Deploy complete!"
