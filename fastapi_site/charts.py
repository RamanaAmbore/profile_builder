"""Plotly chart builders — return JSON strings for client-side rendering."""
from __future__ import annotations

import json
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio

ACCENT_CYAN = "#0891b2"      # cyan-600
ACCENT_INDIGO = "#1d4ed8"    # blue-700
ACCENT_VIOLET = "#059669"    # emerald-600 (token kept as 'violet' for minimal churn)

# Varied palette: mixes blues, cyans, emeralds, violets and purples so charts
# look harmonious rather than a monotone blue-green block.  All shades are
# 600-700 range so white labels remain readable (contrast ≥ 4.5:1).
PALETTE = [
    "#2563eb",  # blue-600
    "#7c3aed",  # violet-600
    "#0891b2",  # cyan-600
    "#4f46e5",  # indigo-600
    "#059669",  # emerald-600
    "#6d28d9",  # purple-700
    "#0284c7",  # sky-600
    "#0f766e",  # teal-700
    "#1d4ed8",  # blue-700
    "#9333ea",  # purple-600
    "#0369a1",  # sky-700
    "#047857",  # emerald-700
    "#4338ca",  # indigo-700
    "#334155",  # slate-700
]


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _wrap_text(text: str, width: int = 40) -> str:
    """Greedy word-wrap hover text so each line is at most `width`
    characters, joined with <br> for Plotly hover templates. Strings
    <= width are returned unchanged. Single words longer than `width`
    are left on their own line rather than broken mid-word."""
    if not text:
        return ""
    text = " ".join(text.split())  # normalize whitespace
    if len(text) <= width:
        return text
    lines: list[str] = []
    current = ""
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "<br>".join(lines)

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#1e293b", size=12),
    margin=dict(l=20, r=20, t=30, b=20),
    # Hover tooltip style mirrors the custom dark popover used on skill
    # cards / cert cards / FRM-CFA badge so all hovers feel consistent.
    hoverlabel=dict(
        bgcolor="#0f172a",          # slate-900
        bordercolor=ACCENT_CYAN,
        font=dict(family="Inter, sans-serif", color="#ffffff", size=11),
        namelength=-1,              # never truncate hover text
        align="left",
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
    # Four distinct hues — one per category, spread across the colour wheel
    category_colors = {
        "Languages":      "#2563eb",  # blue-600
        "Data & Viz":     "#059669",  # emerald-600
        "Backend":        "#7c3aed",  # violet-600
        "Cloud & DevOps": "#0891b2",  # cyan-600
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
            # hoverinfo='none' suppresses Plotly's built-in SVG hover label
            # but still fires plotly_hover events, which our custom HTML
            # #chart-tooltip listens to. hovertemplate would override
            # hoverinfo and re-enable the built-in label, so it's omitted.
            hoverinfo="none",
            text=hovers,
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#1e293b", size=12),
        margin=dict(l=10, r=10, t=8, b=8),
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor=ACCENT_CYAN,
            font=dict(family="Inter, sans-serif", color="#ffffff", size=12),
            namelength=-1,
            align="left",
        ),
        polar=dict(
            domain=dict(x=[0.0, 1.0], y=[0.12, 1.0]),
            bgcolor="rgba(255,255,255,0.92)",
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
            yanchor="top", y=0.08,
            xanchor="center", x=0.5,
            font=dict(color="#1e293b", size=11),
        ),
        height=440,
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
        hoverinfo="none",
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
        hoverinfo="none",
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
        hoverinfo="none",
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
            # Desktop defaults. Client-side JS shrinks these on mobile (<640px).
            size=22,
            color=marker_colors,
            line=dict(color="#ffffff", width=2.5),
            symbol="circle",
        ),
        customdata=labels,
        hovertext=[_wrap_text(h, 40) for h in hovers],
        hoverinfo="none",
    ))
    annotations = [
        dict(
            x=year,
            y=1,
            text=f"<b>{label}</b>",
            showarrow=False,
            yanchor="bottom",
            yshift=14,
            textangle=-90,
            align="left",
            font=dict(color="#0f172a", size=11, family="Inter, sans-serif"),
        )
        for year, label in zip(years, labels)
    ]
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#1e293b", size=12),
        margin=dict(l=8, r=8, t=12, b=4),
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor=ACCENT_CYAN,
            font=dict(family="Inter, sans-serif", color="#ffffff", size=11),
            namelength=-1,
            align="left",
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
            tickfont=dict(size=11, color="#1e293b", family="Inter, sans-serif"),
        ),
        yaxis=dict(visible=False, range=[0.80, 2.40]),
        height=320,
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
