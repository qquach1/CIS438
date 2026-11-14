#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plotly figures for the dashboard, colored for Streamlit's light or dark theme (no data logic here)."""

import html
import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def palette():
    """Colors for the current theme.

    One accent carries every single-series chart. Human and Bot keep the same two hues on every tab,
    HTTP results use the reserved status colors, and the heatmap uses a one-hue blue ramp.
    """
    if st.context.theme.type == "dark":
        return dict(
            dark=True, surface="#0e1117", ink="#f0efec", ink2="#c3c2b7", muted="#898781",
            grid="#2c2c2a", axis="#383835", land="#1d1d1b", coast="#383835",
            accent="#3987e5", human="#3987e5", bot="#d95926", aqua="#199e70", yellow="#c98500",
            gray="#6b6a65", line_gray="#6b6a65",
            ramp=["#141c2b", "#104281", "#2a78d6", "#6da7ec", "#cde2fb"],
            good="#0ca30c", warning="#fab219", critical="#d03b3b", neutral="#6b6a65",
        )
    return dict(
        dark=False, surface="#ffffff", ink="#0b0b0b", ink2="#52514e", muted="#898781",
        grid="#e1e0d9", axis="#c3c2b7", land="#efeee9", coast="#d6d5cf",
        accent="#2a78d6", human="#2a78d6", bot="#eb6834", aqua="#1baf7a", yellow="#eda100",
        gray="#b4b2a9", line_gray="#b4b2a9",
        ramp=["#f1f6fd", "#b7d3f6", "#5598e7", "#256abf", "#0d366b"],
        good="#0ca30c", warning="#fab219", critical="#d03b3b", neutral="#b4b2a9",
    )


# Fills that need near-black text instead of white (palette.md: yellow and the warning status)
DARK_TEXT_FILLS = {"#eda100", "#c98500", "#fab219", "#b4b2a9"}


def shorten(text, limit=44):
    """Cut long URLs in the middle so both the start and the distinguishing end stay readable."""
    text = str(text)
    if len(text) <= limit:
        return text
    keep = (limit - 1) // 2
    return text[:keep] + "…" + text[-(limit - 1 - keep):]


def _style(fig, c, height, legend=False):
    fig.update_layout(
        height=height, margin=dict(t=8, b=8, l=8, r=8), showlegend=legend,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=c["ink2"]),
        hoverlabel=dict(bgcolor=c["surface"], bordercolor=c["axis"], font=dict(color=c["ink"])),
        legend=dict(orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom", title=None,
                    font=dict(color=c["ink2"])),
    )
    fig.update_xaxes(gridcolor=c["grid"], linecolor=c["axis"], zeroline=False, tickfont=dict(color=c["muted"]),
                     title_font=dict(color=c["muted"]))
    fig.update_yaxes(gridcolor=c["grid"], linecolor=c["axis"], zeroline=False, tickfont=dict(color=c["muted"]),
                     title_font=dict(color=c["muted"]))
    return fig


# ── Bars ─────────────────────────────────────────────────────────────────────

def ranked_bars(labels, values, c, hover, customdata=None, colors=None, text=None, names=None):
    """Horizontal bars, largest on top, each labeled at its tip (so the value axis is left off).

    hover is a Plotly hovertemplate; customdata feeds it. colors (one per bar) and names (one legend
    entry per color) are for bars colored by a category, such as 4xx vs 5xx.
    """
    labels, values = list(labels), list(values)
    n = len(values)
    fig = go.Figure()
    shown = []
    for label in labels:  # two long URLs can shorten to the same text; keep every bar its own row
        short = shorten(label)
        while short in shown:
            short += "​"
        shown.append(short)
    text = text if text is not None else [f"{v:,}" for v in values]
    if names is None:
        fig.add_trace(go.Bar(
            y=shown, x=values, orientation="h", marker=dict(color=colors or c["accent"], cornerradius=4),
            text=text, textposition="outside", textfont=dict(color=c["ink"]), cliponaxis=False,
            customdata=customdata, hovertemplate=hover,
        ))
    else:
        # One trace per category so the legend names each color; bars keep their rank order
        for name in dict.fromkeys(names):
            idx = [i for i, nm in enumerate(names) if nm == name]
            fig.add_trace(go.Bar(
                y=[shown[i] for i in idx], x=[values[i] for i in idx], orientation="h", name=name,
                marker=dict(color=colors[idx[0]], cornerradius=4),
                text=[text[i] for i in idx], textposition="outside", textfont=dict(color=c["ink"]),
                cliponaxis=False, hovertemplate=hover,
                customdata=None if customdata is None else [customdata[i] for i in idx],
            ))
    fig.update_yaxes(categoryorder="array", categoryarray=shown[::-1], showgrid=False, ticks="",
                     tickfont=dict(color=c["ink2"]))
    fig.update_xaxes(visible=False, range=[0, (max(values) if values else 1) * 1.04])
    _style(fig, c, height=max(150, 30 * n + 24), legend=names is not None)
    # The right margin holds the value labels, so they never clip however narrow the column gets
    fig.update_layout(bargap=0.35, barmode="overlay", margin=dict(r=60))
    return fig


def columns(x, y, c, hover, customdata=None, yformat=None, ytitle=None, text=None):
    """Vertical bars for one series, such as months. text labels the caps (leave it off for long series)."""
    x, y = list(x), list(y)
    fig = go.Figure(go.Bar(
        x=x, y=y, marker=dict(color=c["accent"], cornerradius=4), customdata=customdata, hovertemplate=hover,
        text=text, textposition="outside", textfont=dict(color=c["ink"]), cliponaxis=False,
    ))
    fig.update_xaxes(type="category", showgrid=False, tickangle=-45 if len(x) > 8 else 0)
    fig.update_yaxes(title=ytitle, rangemode="tozero", tickformat=yformat)
    if text is not None and y:
        fig.update_yaxes(range=[0, max(y) * 1.18])  # headroom for the labels on the caps
    _style(fig, c, height=300)
    fig.update_layout(bargap=0.35)
    return fig


def stacked_columns(x, series, c, hover_unit="requests"):
    """Monthly columns split into parts: series is a list of (name, values, color)."""
    fig = go.Figure()
    for name, values, color in series:
        fig.add_trace(go.Bar(
            x=list(x), y=list(values), name=name,
            marker=dict(color=color, line=dict(color=c["surface"], width=1)),
            hovertemplate=f"{name}: %{{y:,}} {hover_unit}<extra>%{{x}}</extra>",
        ))
    fig.update_xaxes(type="category", showgrid=False, tickangle=-45 if len(x) > 8 else 0)
    fig.update_yaxes(rangemode="tozero")
    _style(fig, c, height=320, legend=True)
    fig.update_layout(barmode="stack", bargap=0.35)
    return fig


# ── Lines & grids ────────────────────────────────────────────────────────────

def daily_trend(daily, c, label, log=False):
    """Each day as a thin gray line, with the 7-day average drawn over it in the accent color.

    The busiest day gets a direct label. On a log scale, days with zero drop out of the gray line.
    """
    avg = daily.rolling(7, min_periods=1).mean()
    # A log axis can't show zero, so quiet days become gaps instead of lines plunging off the chart
    shown_daily, shown_avg = (daily.where(daily > 0), avg.where(avg > 0)) if log else (daily, avg)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily.index, y=shown_daily.values, name="Daily", mode="lines",
        line=dict(color=c["line_gray"], width=1), hovertemplate="%{y:,} " + label + "<extra>Daily</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=avg.index, y=shown_avg.values, name="7-day average", mode="lines",
        line=dict(color=c["accent"], width=2), hovertemplate="%{y:,.1f}<extra>7-day average</extra>",
    ))
    if len(daily) and daily.max() > 0:
        peak, value = daily.idxmax(), daily.max()
        right_half = daily.index.get_loc(peak) > len(daily) / 2  # put the label on the roomier side
        fig.add_annotation(
            x=peak, y=math.log10(value) if log else value, showarrow=False, yanchor="top",
            xanchor="right" if right_half else "left", xshift=-6 if right_half else 6,
            text=f"{peak:%b} {peak.day}, {peak.year}: {value:,}", font=dict(color=c["ink2"], size=12))
    fig.update_xaxes(showgrid=False, hoverformat="%a %b %-d, %Y")
    if log:
        fig.update_yaxes(type="log", dtick=1, tickformat=",d", title=f"{label.capitalize()} (log scale)")
    else:
        fig.update_yaxes(rangemode="tozero", title=label.capitalize())
    _style(fig, c, height=330, legend=True)
    fig.update_layout(hovermode="x unified")
    return fig


def line(x, y, c, hover, yformat=None, ytitle=None):
    """One series over time, 2px with 8px markers ringed in the surface color."""
    fig = go.Figure(go.Scatter(
        x=list(x), y=list(y), mode="lines+markers", line=dict(color=c["accent"], width=2),
        marker=dict(size=8, color=c["accent"], line=dict(color=c["surface"], width=2)), hovertemplate=hover,
    ))
    fig.update_xaxes(type="category", showgrid=False, tickangle=-45 if len(x) > 8 else 0)
    fig.update_yaxes(rangemode="tozero", tickformat=yformat, title=ytitle)
    return _style(fig, c, height=300)


def heatmap(grid, c, clock_label, log=False):
    """Day-of-week by hour grid; grid is a 7 x 24 DataFrame (Mon..Sun by 0..23).

    With log=True the color follows log10(1 + count), and the color bar is still labeled in counts.
    """
    ramp = c["ramp"]
    scale = [[i / (len(ramp) - 1), color] for i, color in enumerate(ramp)]
    hours = [f"{h:02d}:00" for h in range(24)]
    counts = grid.to_numpy()
    colorbar = dict(title=dict(text="Requests", font=dict(color=c["muted"])), thickness=10, outlinewidth=0,
                    tickfont=dict(color=c["muted"]))
    if log:
        ticks = [v for v in (0, 1, 10, 100, 1_000, 10_000, 100_000, 1_000_000) if v <= max(counts.max(), 1)]
        colorbar.update(tickvals=[math.log10(1 + v) for v in ticks], ticktext=[f"{v:,}" for v in ticks])
    fig = go.Figure(go.Heatmap(
        z=np.log10(1 + counts) if log else counts, customdata=counts, x=hours, y=DAY_LABELS,
        colorscale=scale, xgap=2, ygap=2, colorbar=colorbar,
        hovertemplate="%{y} %{x}: %{customdata:,} requests<extra></extra>",
    ))
    fig.update_xaxes(showgrid=False, tickvals=hours[::3], title=f"Hour of day ({clock_label})")
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return _style(fig, c, height=300)


def bubble_map(places, c):
    """One bubble per city, its area proportional to requests. places has city, country, lat/lon, counts."""
    size = places["requests"]
    fig = go.Figure(go.Scattergeo(
        lon=places["longitude"], lat=places["latitude"], mode="markers",
        marker=dict(size=size, sizemode="area", sizeref=2.0 * size.max() / 38 ** 2, sizemin=4,
                    color=c["accent"], opacity=0.75, line=dict(color=c["surface"], width=1)),
        customdata=places[["place", "requests", "visitors"]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,} requests · "
                      "%{customdata[2]:,} visitors<extra></extra>",
    ))
    fig.update_geos(projection_type="natural earth", showframe=False, showcountries=True, showcoastlines=True,
                    countrycolor=c["coast"], coastlinecolor=c["coast"], showland=True, landcolor=c["land"],
                    showocean=False, showlakes=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[-57, 85])
    fig.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)"))
    return _style(fig, c, height=400)


# ── A whole split into parts ─────────────────────────────────────────────────

def segmented_bar(parts, c, title):
    """HTML for a tall segmented bar: one block per part, its share printed inside where it fits.

    parts is a list of (name, value, color). Parts at zero draw nothing. Hovering a block shows its
    exact count; the legend underneath names the blocks in order.
    """
    parts = [(name, value, color) for name, value, color in parts if value > 0]
    total = sum(value for _, value, _ in parts) or 1
    blocks, keys = [], []
    for name, value, color in parts:
        share = value / total
        ink = "#0b0b0b" if color in DARK_TEXT_FILLS else "#ffffff"
        label = f"{share:.0%}" if share >= 0.08 else ""
        tip = html.escape(f"{name}: {value:,} ({share:.1%})")
        blocks.append(
            f'<div title="{tip}" style="flex:{value} 1 0;min-width:3px;height:28px;background:{color};'
            f'color:{ink};border-radius:4px;display:flex;align-items:center;padding:0 8px;'
            f'font-size:0.8rem;font-weight:600;white-space:nowrap;box-sizing:border-box;">{label}</div>')
        keys.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;margin:0 16px 4px 0;">'
            f'<span style="width:10px;height:10px;border-radius:2px;background:{color};"></span>'
            f'{html.escape(name)}</span>')
    summary = html.escape(f"{title}: " + ", ".join(f"{n} {v / total:.1%}" for n, v, _ in parts))
    return (f'<div role="img" aria-label="{summary}">'
            f'<div style="display:flex;gap:2px;width:100%;">{"".join(blocks)}</div>'
            f'<div style="margin-top:8px;font-size:0.85rem;color:{c["ink2"]};display:flex;flex-wrap:wrap;">'
            f'{"".join(keys)}</div></div>')
