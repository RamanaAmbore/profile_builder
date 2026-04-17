# Ramana Ambore — Portfolio

A modern, dynamic portfolio site built with **FastAPI**, **Jinja2**, **Plotly**, **Alpine.js**, and **Tailwind CSS**. All content is driven from a single YAML file — edit the YAML, and everything updates automatically: the web page, interactive charts, dynamically generated PDF resume, plain-text resume, and all SEO meta tags.

Live at **https://ramanaambore.me**.

## What's in the box

| Thing | Where |
|---|---|
| FastAPI app + routes | [fastapi_site/main.py](fastapi_site/main.py) |
| Plotly chart builders (radar, bar, donut, treemap, timeline) | [fastapi_site/charts.py](fastapi_site/charts.py) |
| Dynamic PDF + plain-text resume generation | [fastapi_site/resume_builder.py](fastapi_site/resume_builder.py) |
| Jinja2 templates | [fastapi_site/templates/](fastapi_site/templates/) |
| Tailwind-styled CSS + client JS | [fastapi_site/static/](fastapi_site/static/) |
| Finance/derivatives/Gen AI SVG backdrop | [fastapi_site/static/img/stock-bg.svg](fastapi_site/static/img/stock-bg.svg) |
| All profile content (single source of truth) | [setup/yaml/profile_data.yaml](setup/yaml/profile_data.yaml) |
| Images & resume PDF fallback | [setup/images/](setup/images/), [setup/resume/](setup/resume/) |
| Deployment files (nginx, systemd, webhook) | [deploy/](deploy/) |

## Features

- **Single-page scrolling portfolio** — Hero, About, Career Journey, Skills, Employment, Personal Projects, Education, Certifications, Interests, Contact
- **Interactive Plotly charts** — skills radar grouped by category, employment history bar, education donut, certifications treemap, career timeline with animated hover
- **Custom chart tooltips** — dark rounded popovers on all Plotly charts, consistent with card hover panels (no Plotly built-in labels)
- **Card info panel** — Alpine.js bottom-of-viewport panel that peeks on hover and locks on click for cert cards, education cards, and portfolio articles; shows title, summary, and a CTA link
- **Dynamic resume endpoints** — `GET /resume.pdf` (ReportLab-generated PDF) and `GET /resume.txt` (ATS-friendly plain text), regenerated on every request from YAML
- **SEO + social previews** — Open Graph, Twitter Cards, JSON-LD `Person` + `WebSite` schemas, `hasOccupation`, `hasCredential`, canonical URL, `/robots.txt`, `/sitemap.xml`
- **Recruiter-friendly hero** — animated typewriter role titles, "Open to new opportunities" + "U.S. work authorized" badges, direct email CTA in contact section
- **Responsive** with hamburger mobile nav, touch-friendly tap targets, Intersection-Observer scroll reveals
- **Light theme** with a subtle stock-chart SVG backdrop (option payoff diagrams, Greeks, neural network, bell curve, Black-Scholes formula, ticker strip)
- **Cache-busting** — static assets versioned with server startup timestamp; nginx serves with `immutable` cache control

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

Full deployment instructions and copy-paste config files are in [deploy/README.md](deploy/README.md).

Quick reference:
- Main app systemd unit: [deploy/profile-site.service](deploy/profile-site.service) → `/etc/systemd/system/streamlit_profile_builder.service`
- Deploy script: [deploy/deploy.sh](deploy/deploy.sh) → `/opt/webhook/deploy.sh`
- nginx site config: [deploy/nginx.conf](deploy/nginx.conf) → `/etc/nginx/sites-available/ramanaambore.me`
- Production port: `127.0.0.1:8002` (uvicorn, 2 workers, `User=www-data`)

## Tech stack

- **Python 3.10+** — FastAPI, Uvicorn, Jinja2, PyYAML, Plotly, ReportLab, Markdown
- **Tailwind CSS** (via CDN) — utility-first styling
- **Alpine.js** — lightweight interactivity (mobile nav, hover card panel, typing effect, chart events)
- **Plotly.js** — client-side chart rendering from server-generated JSON
- **nginx** — reverse proxy, HTTPS via Let's Encrypt
- **systemd** — process supervision
- **GitHub webhooks** — continuous deployment on push to `main`
- **Claude Code** — AI-assisted development
