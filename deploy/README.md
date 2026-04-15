# Deployment

Production setup for **https://ramanaambore.me** — FastAPI portfolio served via nginx, managed by systemd, auto-deployed by a GitHub webhook.

## Architecture

```
                     GitHub push to main
                             │
                             │ POST /hooks/deploy   (X-GitHub-Event: push)
                             ▼
                ┌──────────────────────────────┐
                │  https://ramanaambore.me     │
                │  nginx :443                  │
                ├──────────────────────────────┤
                │  /hooks/  → 127.0.0.1:9000  ──┐
                │                               │
                │  /static/ │ /images/          │  adnanh/webhook :9000
                │    (served directly)          │  (webhook.service, www-data)
                │                               ▼
                │  /          → 127.0.0.1:8002  /opt/webhook/deploy.sh
                └──────────────────────────────┘      │
                             ▲                        │ git pull → pip install
                             │                        │ sudo systemctl restart …
                             │                        ▼
                streamlit_profile_builder.service ◄───┘
                  uvicorn :8002, 2 workers, www-data
                             │
                             ▼
                FastAPI + YAML + Plotly + PDF/TXT resume
```

**Key things:**

- The portfolio's webhook listener is its own `adnanh/webhook` instance on port 9000, separate from `ramboq_hook.service` on port 9001 (which belongs to other projects on the same server). Both are independent — never route portfolio-specific traffic through `webhook.ramboq.com`.
- Both the site and the webhook share the domain **ramanaambore.me** — nginx routes `/hooks/*` to the webhook listener and everything else to the FastAPI app.
- The webhook service runs as `www-data` (matching the repo owner) so `git pull` and `pip install` don't rewrite file ownership. It escalates to root only for `systemctl restart streamlit_profile_builder.service` via a narrow sudoers rule.

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
chown www-data:www-data /opt/webhook/deploy.sh
```

### Webhook listener service + sudoers

The adnanh/webhook binary runs as `www-data` on port 9000, reading hooks from `/opt/webhook/hooks.json`:

```ini
# /etc/systemd/system/webhook.service
[Unit]
Description=Webhook GitHub Auto Deploy (portfolio site)
After=network.target

[Service]
User=www-data
Group=www-data
ExecStart=/usr/bin/webhook -hooks /opt/webhook/hooks.json -port 9000 -verbose
Restart=always

[Install]
WantedBy=multi-user.target
```

Narrow sudoers rule so www-data can restart only the portfolio service (put in `/etc/sudoers.d/profile-site-deploy`, mode 440):

```
www-data ALL=(ALL) NOPASSWD: /bin/systemctl restart streamlit_profile_builder.service
```

Then:

```bash
systemctl daemon-reload
systemctl enable --now webhook
```

### Configure the GitHub webhook

In the GitHub repo → **Settings → Webhooks → Add webhook**:

- **Payload URL:** `https://ramanaambore.me/hooks/deploy`
- **Content type:** `application/json`
- **Secret:** *(leave blank or add one — hooks.json currently doesn't verify HMAC; add it for production-grade security)*
- **Events:** Just the `push` event
- **Active:** ✓

After the first install: every `git push origin main` from any machine will:
1. GitHub POSTs to `https://ramanaambore.me/hooks/deploy`
2. nginx proxies to `127.0.0.1:9000`
3. `adnanh/webhook` matches the `deploy` hook (trigger rule: `X-GitHub-Event: push`)
4. Executes `/opt/webhook/deploy.sh`:
   - `git fetch origin main && git reset --hard origin/main`
   - `pip install -r fastapi_site/requirements.txt`
   - `sudo systemctl restart streamlit_profile_builder.service`
5. Site comes back on the new commit within ~60 seconds

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
