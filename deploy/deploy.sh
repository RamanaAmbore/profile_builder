#!/usr/bin/env bash
#
# deploy.sh — pull latest code, install dependencies, restart the portfolio site.
#
# Lives at /opt/webhook/deploy.sh on the server and is triggered by the
# adnanh/webhook listener (hook id "deploy") on every push to main.
#
# The systemd unit is still named `streamlit_profile_builder.service` for
# historical continuity with the /opt/streamlit_profile_builder folder —
# the app it runs is a FastAPI/uvicorn process on port 8002.

set -euo pipefail

REPO_DIR="/opt/streamlit_profile_builder"
VENV_DIR="$REPO_DIR/fastapi_site/.venv"
REQS="$REPO_DIR/fastapi_site/requirements.txt"
SERVICE="streamlit_profile_builder.service"
WEBHOOK_SERVICE="webhook.service"
BRANCH="main"

log() { echo "[$(date -u +%FT%TZ)] $*"; }

cd "$REPO_DIR"

log "Fetching $BRANCH"
git fetch --quiet origin "$BRANCH"
git reset --hard "origin/$BRANCH"

if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating FastAPI virtualenv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

log "Installing dependencies"
"$VENV_DIR/bin/pip" install --quiet --no-cache-dir --upgrade pip
"$VENV_DIR/bin/pip" install --quiet --no-cache-dir -r "$REQS"

log "Restarting $SERVICE"
sudo /bin/systemctl restart "$SERVICE"

# Sync webhook hook definitions. Restart webhook last — it is the parent
# process of this script, so restarting it kills this process. All work
# above is already complete by this point.
HOOKS_SRC="$REPO_DIR/deploy/hooks.json"
HOOKS_DST="/opt/webhook/hooks.json"
if [[ -f "$HOOKS_SRC" ]] && ! diff -q "$HOOKS_SRC" "$HOOKS_DST" &>/dev/null; then
    log "Updating hooks.json and restarting $WEBHOOK_SERVICE"
    cp "$HOOKS_SRC" "$HOOKS_DST"
    sudo /bin/systemctl restart "$WEBHOOK_SERVICE"
fi

log "Deploy complete: $(git rev-parse --short HEAD)"
