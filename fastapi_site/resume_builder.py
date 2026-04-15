"""Dynamic resume generation — PDF (ReportLab) and ATS-friendly plain text."""
from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

ACCENT = HexColor("#0891b2")
INDIGO = HexColor("#1d4ed8")
MUTED = HexColor("#475569")
DARK = HexColor("#0f172a")
LINE = HexColor("#cbd5e1")

_BASE = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=13, textColor=DARK)
NAME = ParagraphStyle("name", parent=_BASE, fontName="Helvetica-Bold", fontSize=22, leading=25, textColor=DARK, spaceAfter=2)
ROLE = ParagraphStyle("role", parent=_BASE, fontSize=12, leading=14, textColor=ACCENT, spaceAfter=3)
CONTACT = ParagraphStyle("contact", parent=_BASE, fontSize=9, leading=11, textColor=MUTED, spaceAfter=0)
SECTION = ParagraphStyle("section", parent=_BASE, fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=INDIGO, spaceBefore=10, spaceAfter=5)
SUB = ParagraphStyle("sub", parent=_BASE, fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=DARK, spaceBefore=6, spaceAfter=1)
META = ParagraphStyle("meta", parent=_BASE, fontSize=9, leading=11, textColor=MUTED, spaceAfter=2)
BODY = ParagraphStyle("body", parent=_BASE, fontSize=9.5, leading=13, textColor=DARK, spaceAfter=4, alignment=TA_LEFT)
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=14, bulletIndent=2, spaceAfter=2)
TECH = ParagraphStyle("tech", parent=_BASE, fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=MUTED, leftIndent=14, spaceAfter=4)


def _clean(s: str | None) -> str:
    if not s:
        return ""
    return (
        s.replace("`", "")
        .replace("\u2013", "-")
        .replace("\u2014", "—")
        .replace("\xa0", " ")
        .strip()
    )


def _hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=4, spaceAfter=6)


def build_pdf(d: dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title=f"{d.get('name', '').title()} — Resume",
        author=d.get("name", "").title(),
        subject="Resume",
    )

    story: list = []

    suffix = d.get("name suffix", "")
    name_text = d.get("name", "").upper()
    if suffix:
        name_text = f"{name_text}, {suffix}"
    story.append(Paragraph(name_text, NAME))
    story.append(Paragraph(d.get("designation", "").title(), ROLE))

    contact = d.get("contact", {})
    bits = []
    for k in ("mail", "phone", "loc"):
        if k in contact:
            bits.append(_clean(contact[k].get("label", "")))
    social = d.get("social", {})
    for k in ("linkedin", "github", "medium"):
        if k in social:
            bits.append(social[k].get("link", ""))
    story.append(Paragraph("  |  ".join(b for b in bits if b), CONTACT))
    story.append(_hr())

    story.append(Paragraph("PROFESSIONAL SUMMARY", SECTION))
    story.append(Paragraph(_clean(d.get("profile", "")), BODY))

    story.append(Paragraph("KEY ACHIEVEMENTS", SECTION))
    for item in d.get("experience summary", []):
        story.append(Paragraph(f"• {_clean(item)}", BULLET))

    story.append(Paragraph("CORE TECHNICAL SKILLS", SECTION))
    skills = d.get("technical skills", {})
    skill_names = [s for s in skills.keys()]
    if skill_names:
        story.append(Paragraph(", ".join(skill_names), BODY))

    story.append(Paragraph("PROFESSIONAL EXPERIENCE", SECTION))
    for company, meta in d.get("projects", {}).items():
        story.append(Paragraph(f"<b>{company}</b>", SUB))
        story.append(Paragraph(_clean(meta.get("long label", "")), META))
        for client, projs in meta.get("clients", {}).items():
            for pname, proj in projs.items():
                role = proj.get("role", "")
                start = proj.get("start", "")
                end = proj.get("end", "")
                dates = f" ({start} – {end})" if start else ""
                header = f"<i>{pname}</i>"
                if role:
                    header += f" — {role}"
                if dates:
                    header += dates
                story.append(Paragraph(header, BULLET))
                if proj.get("summary"):
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{_clean(proj['summary'])}", BULLET))
                if proj.get("technology"):
                    story.append(Paragraph(f"Tech: {_clean(proj['technology'])}", TECH))

    story.append(Paragraph("EDUCATION", SECTION))
    for name, ed in d.get("education", {}).items():
        story.append(Paragraph(f"<b>{name}</b> — {_clean(ed.get('long label', ''))}", BULLET))

    story.append(Paragraph("CERTIFICATIONS", SECTION))
    for name, c in d.get("certifications", {}).items():
        story.append(Paragraph(f"<b>{name}</b> — {_clean(c.get('long label', ''))}", BULLET))

    doc.build(story)
    return buf.getvalue()


def build_txt(d: dict[str, Any]) -> str:
    lines: list[str] = []

    def rule(char: str = "=") -> None:
        lines.append(char * 80)

    def section(title: str) -> None:
        lines.append("")
        rule("=")
        lines.append(title.upper())
        rule("=")

    suffix = d.get("name suffix", "")
    name = d.get("name", "").upper()
    if suffix:
        name = f"{name}, {suffix}"
    lines.append(name)
    lines.append(d.get("designation", "").title())
    lines.append("")

    contact = d.get("contact", {})
    if "mail" in contact:
        lines.append(f"Email:    {_clean(contact['mail'].get('label', ''))}")
    if "phone" in contact:
        lines.append(f"Phone:    {_clean(contact['phone'].get('label', ''))}")
    if "loc" in contact:
        lines.append(f"Location: {_clean(contact['loc'].get('label', ''))}")
    social = d.get("social", {})
    if "linkedin" in social:
        lines.append(f"LinkedIn: {social['linkedin'].get('link', '')}")
    if "github" in social:
        lines.append(f"GitHub:   {social['github'].get('link', '')}")
    if "medium" in social:
        lines.append(f"Medium:   {social['medium'].get('link', '')}")

    section("Professional Summary")
    lines.append(_clean(d.get("profile", "")))

    section("Key Achievements")
    for item in d.get("experience summary", []):
        lines.append(f"- {_clean(item)}")

    section("Core Technical Skills")
    for sname, skill in d.get("technical skills", {}).items():
        dur = skill.get("duration", 0)
        lvl = skill.get("level", 0)
        lines.append(f"- {sname} ({dur}+ yrs, level {lvl}/5)")

    section("Professional Experience")
    for company, meta in d.get("projects", {}).items():
        lines.append("")
        lines.append(company.upper())
        lines.append(_clean(meta.get("long label", "")))
        lines.append("-" * 80)
        for client, projs in meta.get("clients", {}).items():
            lines.append(f"Client: {client}")
            for pname, proj in projs.items():
                lines.append("")
                lines.append(f"  {pname}")
                if proj.get("role"):
                    lines.append(f"    Role:       {proj['role']}")
                if proj.get("start"):
                    lines.append(f"    Duration:   {proj.get('start', '')} - {proj.get('end', '')}")
                if proj.get("technology"):
                    lines.append(f"    Technology: {proj['technology']}")
                if proj.get("summary"):
                    lines.append("")
                    summary = _clean(proj["summary"])
                    for para in summary.split("\n"):
                        if para.strip():
                            lines.append(f"    {para.strip()}")

    section("Education")
    for name, ed in d.get("education", {}).items():
        lines.append(f"- {_clean(ed.get('long label', ''))}")

    section("Certifications")
    for name, c in d.get("certifications", {}).items():
        lines.append(f"- {_clean(c.get('long label', ''))}")

    lines.append("")
    lines.append("-" * 80)
    lines.append("Generated dynamically from profile_data.yaml")
    return "\n".join(lines) + "\n"
