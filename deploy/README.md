# Deployment

Production setup for **https://ramanaambore.me** — FastAPI portfolio served via nginx, managed by systemd, auto-deployed by a GitHub webhook.

## Architecture

```
GitHub push to main
        │
        │ POST (X-GitHub-Event: push)
        ▼
  adnanh/webhook :9000 ──▶ /opt/webhook/deploy.sh
        │                        │
        │                        │ git pull, pip install
        │                        │ systemctl restart streamlit_profile_builder
        ▼                        ▼
  nginx :443  ──────────▶  systemd: streamlit_profile_builder.service
                                   │
                                   ▼
                             uvicorn :8002
                                   │
                                   ▼
                             FastAPI + YAML + Plotly
```

## Files in this folder

| File | Target on server |
|---|---|
| [profile-site.service](profile-site.service) | `/etc/systemd/system/streamlit_profile_builder.service` |
| [nginx.conf](nginx.conf) | `/etc/nginx/sites-available/ramanaambore.me` |
| [deploy.sh](deploy.sh) | `/opt/webhook/deploy.sh` |

The systemd unit name and the `/opt/streamlit_profile_builder/` directory keep their historical "streamlit" names purely for compatibility with the existing server setup — the application itself is a modern FastAPI app, no Streamlit involved.

## Port allocation on this server

| Port | Process | Served via |
|---|---|---|
| **8002** | uvicorn (FastAPI portfolio — this project) | `ramanaambore.me` |
| 8000 | uvicorn (ramboq backend) | `ramboq.com` |
| 8501 | _(previously Streamlit — removed)_ | — |
| 9000 | adnanh/webhook — streamlit_profile_builder hooks | internal |
| 9001 | adnanh/webhook — ramboq hooks | `webhook.ramboq.com` |

## Install / update on the server

Run as root (or via `sudo`):

```bash
cd /opt/streamlit_profile_builder

# Pull latest code
git fetch origin main
git reset --hard origin/main

# Create / refresh the FastAPI virtualenv
python3 -m venv fastapi_site/.venv
fastapi_site/.venv/bin/pip install --upgrade pip
fastapi_site/.venv/bin/pip install -r fastapi_site/requirements.txt

# Install / update systemd unit
cp deploy/profile-site.service /etc/systemd/system/streamlit_profile_builder.service
systemctl daemon-reload
systemctl enable --now streamlit_profile_builder

# Install / update nginx site
cp deploy/nginx.conf /etc/nginx/sites-available/ramanaambore.me
nginx -t && systemctl reload nginx

# Install / update the webhook deploy hook
cp deploy/deploy.sh /opt/webhook/deploy.sh
chmod +x /opt/webhook/deploy.sh
```

After the first install: every `git push origin main` from any machine will:
1. Hit the existing `/hooks/deploy` endpoint on the adnanh/webhook listener
2. Trigger `/opt/webhook/deploy.sh`
3. `git reset --hard origin/main`, `pip install`, `systemctl restart streamlit_profile_builder`

## Daily operations

```bash
# Tail app logs
journalctl -u streamlit_profile_builder -f

# Manually deploy (by hand, without waiting for webhook)
bash /opt/webhook/deploy.sh

# Restart the app
systemctl restart streamlit_profile_builder

# Check it's healthy
curl -sI http://127.0.0.1:8002/ | head -1

# Reload nginx after editing the site config
nginx -t && systemctl reload nginx
```

## Troubleshooting

**502 Bad Gateway** — `streamlit_profile_builder` service is down. Check `journalctl -u streamlit_profile_builder -n 100` for the traceback and `systemctl restart streamlit_profile_builder`.

**Static / image assets 404** — nginx `alias` paths point at `/opt/streamlit_profile_builder/{fastapi_site/static,setup/images}/`. Make sure the directories exist and are readable by `www-data`.

**Port collision** — if `streamlit_profile_builder.service` refuses to start because 8002 is in use, find the squatter with `ss -tlnp | grep :8002` and stop it (or change the port in both `profile-site.service` and `nginx.conf`).

**Webhook didn't trigger** — check `systemctl status webhook` and `journalctl -u webhook -n 50`. Verify the hook id in `/opt/webhook/hooks.json` matches what GitHub is hitting and that the hook trigger rule matches the push event.

**Resume PDF / text endpoints look stale** — both are regenerated on every request from `setup/yaml/profile_data.yaml`. If your YAML edit didn't show up, the git pull probably didn't happen — check the webhook logs.
