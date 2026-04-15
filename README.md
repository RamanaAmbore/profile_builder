# Ramana Ambore — Portfolio

A modern, dynamic profile / portfolio website built with **FastAPI**, **Jinja2**, **Plotly**, and **Tailwind CSS**. All content is driven from a single YAML file — edit the YAML, everything (web page, dynamic PDF resume, plain-text resume, SEO meta tags, structured data) updates automatically.

Live at **https://ramanaambore.me**.

## What's in the box

| Thing | Where |
|---|---|
| FastAPI app + routes | [fastapi_site/main.py](fastapi_site/main.py) |
| Plotly charts (radar, bar, donut, timeline) | [fastapi_site/charts.py](fastapi_site/charts.py) |
| Dynamic PDF + plain-text resume generation | [fastapi_site/resume_builder.py](fastapi_site/resume_builder.py) |
| Jinja2 templates | [fastapi_site/templates/](fastapi_site/templates/) |
| Tailwind-styled CSS + client JS | [fastapi_site/static/](fastapi_site/static/) |
| Background SVG (finance + derivatives + Gen AI motifs) | [fastapi_site/static/img/stock-bg.svg](fastapi_site/static/img/stock-bg.svg) |
| All profile content (single source of truth) | [setup/yaml/profile_data.yaml](setup/yaml/profile_data.yaml) |
| Images & resume PDF fallback | [setup/images/](setup/images/), [setup/resume/](setup/resume/) |
| Deployment files (nginx, systemd, webhook) | [deploy/](deploy/) |

## Features

- **Single-page scrolling portfolio** — Hero, About, Career Journey, Skills, Employment, Personal Projects, Education, Certifications, Interests, Contact
- **Interactive Plotly charts** — skills radar grouped by category, employment bar, education donut, career timeline with horizontal grid rails
- **Dynamic resume endpoints** — `GET /resume.pdf` (ReportLab-generated PDF) and `GET /resume.txt` (ATS-friendly plain text), both regenerated from YAML on every request
- **SEO + social previews** — Open Graph, Twitter cards, JSON-LD `Person` schema, canonical URL, `/robots.txt`, `/sitemap.xml`
- **Responsive** with hamburger mobile nav, touch-friendly tap targets, Intersection-Observer-driven scroll reveals
- **Hover preview cards** on the FRM / CFA credential links (pulls from the YAML cert data)
- **Clickable cert cards** — each certification opens the credential's official verification URL
- **Light theme** with a subtle stock-chart SVG backdrop featuring option payoff diagrams, Greek letters, a small neural network, bell curve, Black-Scholes formula, and a ticker strip — a quiet nod to finance + derivatives + Gen AI

## Run locally

```bash
cd fastapi_site
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload
# open http://127.0.0.1:8000
```

Edit [setup/yaml/profile_data.yaml](setup/yaml/profile_data.yaml) and refresh — the page, the PDF at `/resume.pdf`, and the plain-text resume at `/resume.txt` all update from the same source.

## Deployment (production)

The site runs on a Linux server behind **nginx** (reverse proxy + HTTPS termination) with **systemd** managing the uvicorn process. Continuous deployment is handled by the [adnanh/webhook](https://github.com/adnanh/webhook) listener: on every push to `main`, a hook fires [deploy/deploy.sh](deploy/deploy.sh), which pulls the repo, installs dependencies, and restarts the service.

Full deployment instructions + copy-paste-ready config files are in [deploy/README.md](deploy/README.md).

Quick reference:
- Main app systemd unit: [deploy/profile-site.service](deploy/profile-site.service) → `/etc/systemd/system/streamlit_profile_builder.service`
- Deploy script: [deploy/deploy.sh](deploy/deploy.sh) → `/opt/webhook/deploy.sh`
- nginx site config: [deploy/nginx.conf](deploy/nginx.conf) → `/etc/nginx/sites-available/ramanaambore.me`
- Production port: `127.0.0.1:8002` (uvicorn, 2 workers, `User=www-data`)

## Tech stack

- **Python 3.10+** — FastAPI, Uvicorn, Jinja2, PyYAML, Plotly, ReportLab, Markdown
- **Tailwind CSS** (via CDN) — utility-first styling
- **Alpine.js** — lightweight interactivity (mobile nav, hover popovers, typing effect)
- **Plotly.js** — client-side chart rendering from server-generated JSON
- **nginx** — reverse proxy, HTTPS
- **systemd** — process supervision
- **GitHub webhooks** — continuous deployment on push
