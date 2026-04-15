"""FastAPI server for the profile site."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import markdown as md
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from charts import build_all
from resume_builder import build_pdf, build_txt

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
SETUP = PROJECT_ROOT / "setup"
YAML_PATH = SETUP / "yaml" / "profile_data.yaml"
IMAGES_DIR = SETUP / "images"
RESUME_DIR = SETUP / "resume"

# Public site URL — set PUBLIC_SITE_URL env var after deployment so social
# previews use the live domain instead of the request host.
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "https://ramanaambore.me").rstrip("/")

app = FastAPI(title="Ramana Ambore — Portfolio")

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
app.mount("/resume", StaticFiles(directory=RESUME_DIR), name="resume")

templates = Jinja2Templates(directory=ROOT / "templates")


def _md(text: str | None) -> str:
    if not text:
        return ""
    return md.markdown(text.strip(), extensions=["extra", "nl2br"])


templates.env.filters["md"] = _md


def load_profile() -> dict[str, Any]:
    with YAML_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_seo(data: dict[str, Any]) -> dict[str, str]:
    name = str(data.get("name", "")).title()
    designation = str(data.get("designation", "")).title()
    loc = data.get("contact", {}).get("loc", {}).get("label", "")
    title = f"{name} — {designation}"
    description = (
        f"{name} — {designation}. FRM-certified FinTech professional based in "
        f"{loc}. 30+ years modernizing legacy systems, optimizing trading platforms, "
        f"and developing algorithmic trading solutions."
    )
    keywords = (
        "Ramana Ambore, FRM, CFA, FinTech, Application Development Director, "
        "Java, Python, AWS, COBOL modernization, algorithmic trading, Merrimack NH"
    )
    return {
        "title": title,
        "description": description,
        "keywords": keywords,
        "image": f"{PUBLIC_SITE_URL}/images/profile_photo.png",
        "url": PUBLIC_SITE_URL + "/",
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    data = load_profile()
    charts = build_all(data)
    total_years = sum(p.get("duration", 0) for p in data.get("projects", {}).values())
    stats = {
        "years": total_years,
        "skills": len(data.get("technical skills", {})),
        "certs": len(data.get("certifications", {})),
        "projects": sum(len(p.get("clients", {})) for p in data.get("projects", {}).values()),
    }
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "d": data,
            "charts": charts,
            "stats": stats,
            "seo": build_seo(data),
        },
    )


@app.get("/resume.pdf")
def resume_pdf():
    data = load_profile()
    pdf_bytes = build_pdf(data)
    filename = "ramana-ambore-resume.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=300",
        },
    )


@app.get("/resume.txt", response_class=PlainTextResponse)
def resume_txt():
    data = load_profile()
    return build_txt(data)


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return f"User-agent: *\nAllow: /\nSitemap: {PUBLIC_SITE_URL}/sitemap.xml\n"


@app.get("/sitemap.xml")
def sitemap():
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{PUBLIC_SITE_URL}/</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>\n'
        '</urlset>\n'
    )
    from fastapi.responses import Response
    return Response(content=xml, media_type="application/xml")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
