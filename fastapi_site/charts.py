"""Plotly chart builders — return JSON strings for client-side rendering."""
from __future__ import annotations

import json
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio

ACCENT_CYAN = "#0891b2"      # cyan-600
ACCENT_INDIGO = "#1d4ed8"    # blue-700
ACCENT_VIOLET = "#059669"    # emerald-600 (token kept as 'violet' for minimal churn)
ACCENT_PINK = "#475569"      # slate-600
ACCENT_EMERALD = "#10b981"   # emerald-500
ACCENT_AMBER = "#64748b"     # slate-500

# Darker blue/green/teal/slate palette — chosen so white labels read clearly
PALETTE = [
    "#0e7490",  # cyan-700
    "#1d4ed8",  # blue-700
    "#047857",  # emerald-700
    "#0d9488",  # teal-600
    "#0891b2",  # cyan-600
    "#1e40af",  # blue-800
    "#059669",  # emerald-600
    "#0f766e",  # teal-700
    "#155e75",  # cyan-800
    "#065f46",  # emerald-800
    "#2563eb",  # blue-600
    "#0369a1",  # sky-700
    "#064e3b",  # emerald-900
    "#334155",  # slate-700
]


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _wrap_text(text: str, width: int = 40) -> str:
    """Wrap hover text into EXACTLY two lines when it exceeds `width`
    characters. Splits at the word boundary nearest the middle so both
    lines end up roughly balanced. Strings <= width are returned as-is."""
    if not text:
        return ""
    text = " ".join(text.split())  # normalize whitespace
    if len(text) <= width:
        return text

    mid = len(text) // 2
    # Search outward from the middle for the closest space
    best = -1
    for offset in range(mid + 1):
        left = mid - offset
        right = mid + offset
        if 0 < left < len(text) and text[left] == " ":
            best = left
            break
        if right < len(text) and text[right] == " ":
            best = right
            break
    if best == -1:
        return text  # pathological: no spaces
    return text[:best] + "<br>" + text[best + 1 :]

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#1e293b", size=12),
    margin=dict(l=20, r=20, t=30, b=20),
    hoverlabel=dict(
        bgcolor="#ffffff",
        bordercolor=ACCENT_CYAN,
        font=dict(family="Inter, sans-serif", color="#0f172a", size=12),
        namelength=-1,  # never truncate hover text
    ),
)


def _to_json(fig: go.Figure) -> str:
    return pio.to_json(fig)


SKILL_CATEGORIES = {
    "Languages": ["python", "java", "COBOL"],
    "Data & Viz": ["snowflake", "streamlit", "dash/plotly", "spark"],
    "Backend": ["SpringBoot", "CICS", "DB2/SQL", "JCL", "VSAM"],
    "Cloud & DevOps": ["AWS", "terraform", "jenkins", "git", "claude code"],
}


def skills_radar(skills: dict[str, dict[str, Any]]) -> str:
    fig = go.Figure()
    # Distinct darker shades per category — legible legend + strong contrast
    category_colors = {
        "Languages":      "#0e7490",  # cyan-700
        "Data & Viz":     "#047857",  # emerald-700
        "Backend":        "#1d4ed8",  # blue-700
        "Cloud & DevOps": "#0d9488",  # teal-600
    }
    for category, skill_names in SKILL_CATEGORIES.items():
        present = [s for s in skill_names if s in skills]
        if not present:
            continue
        levels = [skills[s]["level"] for s in present]
        hovers = [_wrap_text(skills[s].get("hover", ""), 40) for s in present]
        labels = [s.upper() for s in present]
        levels.append(levels[0])
        labels.append(labels[0])
        hovers.append(hovers[0])
        color = category_colors.get(category, ACCENT_CYAN)
        fig.add_trace(go.Scatterpolar(
            r=levels,
            theta=labels,
            name=category,
            fill="toself",
            line=dict(color=color, width=2.5),
            fillcolor=_hex_to_rgba(color, 0.22),
            marker=dict(size=6, color=color, line=dict(color="#ffffff", width=1.5)),
            hovertemplate="<b>%{theta}</b><br>Level: %{r}/5<br>%{text}<extra>" + category + "</extra>",
            text=hovers,
        ))
    fig.update_layout(
        **BASE_LAYOUT,
        polar=dict(
            bgcolor="rgba(248,250,252,0.7)",
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                gridcolor="rgba(100,116,139,0.25)",
                linecolor="rgba(100,116,139,0.35)",
                tickfont=dict(color="#475569", size=10),
            ),
            angularaxis=dict(
                gridcolor="rgba(100,116,139,0.22)",
                linecolor="rgba(100,116,139,0.35)",
                tickfont=dict(color="#1e293b", size=11, family="Inter, sans-serif"),
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.15,
            xanchor="center", x=0.5,
            font=dict(color="#1e293b", size=12),
        ),
        height=520,
    )
    return _to_json(fig)


def employment_bar(projects: dict[str, dict[str, Any]]) -> str:
    companies = []
    durations = []
    hovers = []
    for name, meta in projects.items():
        short = meta.get("short label") or meta.get("label") or name.split(" (")[0]
        companies.append(short)
        durations.append(meta.get("duration", 0))
        hovers.append(_wrap_text(meta.get("hover", meta.get("long label", "")), 40))
    bar_colors = [PALETTE[i % len(PALETTE)] for i in range(len(companies))]
    fig = go.Figure(go.Bar(
        x=durations,
        y=companies,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color="rgba(255,255,255,0.9)", width=1.5),
        ),
        text=[f"{d} yr" for d in durations],
        textposition="outside",
        textfont=dict(color="#1e293b", size=12, family="Inter, sans-serif"),
        hovertext=hovers,
        hovertemplate="<b>%{y}</b><br>%{hovertext}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        xaxis=dict(
            title=dict(text="Years", font=dict(color="#334155", size=11)),
            gridcolor="rgba(100,116,139,0.22)",
            zerolinecolor="rgba(100,116,139,0.30)",
            color="#334155",
            tickfont=dict(color="#334155", size=11),
        ),
        yaxis=dict(
            gridcolor="rgba(100,116,139,0.15)",
            color="#0f172a",
            tickfont=dict(color="#0f172a", size=12, family="Inter, sans-serif"),
            autorange="reversed",
        ),
        height=360,
        showlegend=False,
    )
    return _to_json(fig)


def education_donut(education: dict[str, dict[str, Any]]) -> str:
    labels = [e for e in education]
    values = [education[e].get("duration", 1) for e in labels]
    hovers = [education[e].get("hover", "") for e in labels]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker=dict(
            colors=PALETTE[: len(labels)],
            line=dict(color="#ffffff", width=3),
        ),
        textfont=dict(color="#ffffff", size=13, family="Inter, sans-serif"),
        hovertext=hovers,
        hovertemplate="<b>%{label}</b><br>%{hovertext}<extra></extra>",
        textinfo="label",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        showlegend=False,
        height=360,
        annotations=[dict(
            text="<b>EDU</b><br><span style='font-size:11px;color:#64748b'>3 degrees</span>",
            x=0.5, y=0.5, font=dict(size=18, color=ACCENT_INDIGO), showarrow=False,
        )],
    )
    return _to_json(fig)


def certifications_treemap(certs: dict[str, dict[str, Any]]) -> str:
    labels = list(certs.keys())
    values = [certs[c].get("duration", 100) for c in labels]
    hovers = [certs[c].get("hover", "") for c in labels]
    groups = [certs[c].get("group", "other").title() for c in labels]
    cell_colors = [PALETTE[i % len(PALETTE)] for i in range(len(labels))]
    fig = go.Figure(go.Treemap(
        labels=labels,
        values=values,
        parents=[""] * len(labels),
        marker=dict(
            colors=cell_colors,
            line=dict(color="#ffffff", width=3),
        ),
        text=[f"{g}<br>{v}h" for g, v in zip(groups, values)],
        textfont=dict(color="#ffffff", size=14, family="Inter, sans-serif"),
        hovertext=hovers,
        hovertemplate="<b>%{label}</b><br>%{hovertext}<extra></extra>",
        textinfo="label+text",
    ))
    fig.update_layout(**BASE_LAYOUT, height=360)
    return _to_json(fig)


def career_timeline(milestones: dict[int, dict[str, Any]]) -> str:
    years = sorted(milestones.keys())
    labels = [milestones[y]["milestone"] for y in years]
    hovers = [milestones[y]["hover"] for y in years]
    fig = go.Figure()
    marker_colors = [PALETTE[i % len(PALETTE)] for i in range(len(years))]

    # Horizontal grid lines behind the bubbles — subtle rails of context
    grid_ys = [0.80, 0.90, 1.00, 1.10, 1.20]
    for gy in grid_ys:
        fig.add_shape(
            type="line",
            x0=min(years) - 1, x1=max(years) + 1, y0=gy, y1=gy,
            line=dict(
                color="rgba(100,116,139,0.22)" if gy != 1.00 else "rgba(8,145,178,0.55)",
                width=1 if gy != 1.00 else 2.5,
                dash="dot" if gy != 1.00 else "solid",
            ),
            layer="below",
        )

    fig.add_trace(go.Scatter(
        x=years,
        y=[1] * len(years),
        mode="markers",
        marker=dict(
            size=10,
            color=marker_colors,
            line=dict(color="#ffffff", width=1.5),
            symbol="circle",
        ),
        customdata=labels,
        hovertext=[_wrap_text(h, 40) for h in hovers],
        hovertemplate="<b>%{x} — %{customdata}</b><br>%{hovertext}<extra></extra>",
    ))
    annotations = [
        dict(
            x=year,
            y=1,
            text=f"<b>{label}</b>",
            showarrow=False,
            yanchor="bottom",
            yshift=7,
            textangle=-90,
            align="left",
            font=dict(color="#0f172a", size=8, family="Inter, sans-serif"),
        )
        for year, label in zip(years, labels)
    ]
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#1e293b", size=10),
        margin=dict(l=4, r=4, t=8, b=4),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor=ACCENT_CYAN,
            font=dict(family="Inter, sans-serif", color="#0f172a", size=11),
            namelength=-1,
        ),
        xaxis=dict(
            title="",
            gridcolor="rgba(100,116,139,0.18)",
            color="#334155",
            range=[min(years) - 1, max(years) + 1],
            tickmode="array",
            tickvals=years,
            ticktext=[str(y) for y in years],
            tickangle=-90,
            tickfont=dict(size=8, color="#1e293b", family="Inter, sans-serif"),
        ),
        yaxis=dict(visible=False, range=[0.85, 2.20]),
        height=240,
        showlegend=False,
        annotations=annotations,
    )
    return _to_json(fig)


def build_all(data: dict[str, Any]) -> dict[str, str]:
    return {
        "skills": skills_radar(data.get("technical skills", {})),
        "employment": employment_bar(data.get("projects", {})),
        "education": education_donut(data.get("education", {})),
        "certifications": certifications_treemap(data.get("certifications", {})),
        "timeline": career_timeline(data.get("milestones", {})),
    }
