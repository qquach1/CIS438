#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from grading import GPA_POINTS, LETTERS, NEXT_UP, SHIFT_STEP, band_table, score_stats
from sidebar import set_cutoffs


def chart_colors():
    """One accent for data marks plus ink colors, picked for Streamlit's light or dark theme."""
    if st.context.theme.type == "dark":
        return dict(mark="#3987e5", surface="#0e1117", ink="#f0efec", muted="#898781",
                    band="rgba(255,255,255,0.05)", critical="#d03b3b")
    return dict(mark="#2a78d6", surface="#ffffff", ink="#0b0b0b", muted="#898781",
                band="rgba(11,11,11,0.04)", critical="#d03b3b")


# ── Headline numbers ─────────────────────────────────────────────────────────

def render_summary(graded, n_withdrawn, cap, best):
    mean_gpa = graded["GPA"].mean()
    # Fixed-width tiles in a horizontal container wrap onto a second row instead of squeezing
    tile = dict(border=True, width=170)
    with st.container(horizontal=True, gap="xsmall", horizontal_alignment="distribute"):
        # delta_color="inverse": landing under the cap shows green, going over shows red
        st.metric("Mean GPA", mean_gpa, delta=round(mean_gpa - cap, 3), delta_color="inverse",
                  delta_description="vs cap", format="%.3f", **tile)
        st.metric("Median GPA", graded["GPA"].median(), format="%.2f", **tile)
        st.metric("Students graded", len(graded), **tile,
                  help=f"{n_withdrawn} all-zero students left out as withdrawn." if n_withdrawn else None)
        st.metric("Average total", graded["Total"].mean(), format="%.1f", **tile)
        st.metric("A or A- share", f"{graded['Letter'].isin(['A', 'A-']).mean():.0%}", **tile)

    if mean_gpa <= cap + 1e-9:
        message = f"**Within the cap.** The mean GPA is {mean_gpa:.3f}, {cap - mean_gpa:.3f} under the {cap:.2f} limit."
        if best is not None and best["Shift"] < 0:
            message += f" Every cutoff could drop by up to {-best['Shift']:g} points and still meet it."
        st.success(message, icon=":material/check_circle:")
    else:
        message = f"**Over the cap.** The mean GPA is {mean_gpa:.3f}, {mean_gpa - cap:.3f} above the {cap:.2f} limit."
        if best is not None:
            message += f" Raising every cutoff by {best['Shift']:g} points brings it to {best['Mean GPA']:.3f}."
        st.error(message, icon=":material/error:")


# ── Distribution tab ─────────────────────────────────────────────────────────

def score_dots(graded, cutoffs, max_score, c):
    """One dot per student along the total-score axis, stacked within each whole point."""
    dots = graded.sort_values("Total")
    stack = dots.groupby(dots["Total"] // 1).cumcount()
    # A total exactly on a cutoff earns the higher grade, so nudge it to that side of the line
    x = dots["Total"] + dots["Total"].isin(list(cutoffs.values())) * max_score / 250
    pad = max_score * 0.02

    fig = go.Figure(go.Scatter(
        x=x, y=stack, mode="markers",
        marker=dict(size=10, color=c["mark"], line=dict(width=2, color=c["surface"])),
        customdata=dots[["Student", "Total", "Letter"]],
        hovertemplate="<b>%{customdata[0]}</b><br>Total %{customdata[1]}<br>Grade %{customdata[2]}<extra></extra>",
    ))
    # Shade every other grade band and label each one with its letter
    edges = [max_score + pad] + [cutoffs[letter] for letter in LETTERS[:-1]] + [-pad]
    for i, letter in enumerate(LETTERS):
        top, bottom = edges[i], edges[i + 1]
        if top <= bottom:
            continue  # cutoffs out of order, so nobody can land in this band
        if i % 2 == 0:
            fig.add_vrect(x0=bottom, x1=top, fillcolor=c["band"], line_width=0, layer="below")
        fig.add_annotation(x=(top + bottom) / 2, y=1, yref="paper", yanchor="bottom", text=letter,
                           showarrow=False, font=dict(color=c["ink"], size=13))
    for letter in LETTERS[:-1]:
        fig.add_vline(x=cutoffs[letter], line=dict(color=c["muted"], width=1, dash="dot"))

    fig.update_xaxes(title="Total score", range=[-pad, max_score + pad], showgrid=False, zeroline=False)
    fig.update_yaxes(visible=False, range=[-0.8, max(stack.max(), 3) + 0.8])
    fig.update_layout(height=320, margin=dict(t=30, b=10, l=10, r=10), showlegend=False)
    return fig


def letter_bars(bands, c):
    """Students per grade. Every bar carries its count, so the y-axis is left off."""
    fig = go.Figure(go.Bar(
        x=bands["Grade"], y=bands["Students"],
        marker=dict(color=c["mark"], cornerradius=4),
        text=bands["Students"], textposition="outside", textfont=dict(color=c["ink"]), cliponaxis=False,
        customdata=bands["Share"],
        hovertemplate="%{x}: %{y} students (%{customdata:.0%})<extra></extra>",
    ))
    fig.update_xaxes(type="category", title=None)
    fig.update_yaxes(visible=False, range=[0, max(bands["Students"].max(), 1) * 1.15])
    fig.update_layout(height=320, bargap=0.45, margin=dict(t=30, b=10, l=10, r=10), showlegend=False)
    return fig


def render_distribution(graded, cutoffs, max_score):
    c = chart_colors()
    bands = band_table(graded, cutoffs)

    # Full width, so the crowded 80-100 range has room to spread out
    st.subheader("Where each student lands")
    st.plotly_chart(score_dots(graded, cutoffs, max_score, c))
    st.caption("One dot per student; hover for names. Dotted lines are the cutoffs.")

    col1, col2 = st.columns((1, 1.8))
    with col1:
        st.subheader("Students per grade")
        st.plotly_chart(letter_bars(bands, c))
    with col2:
        st.subheader("Grade bands")
        st.dataframe(bands.assign(Share=bands["Share"] * 100), hide_index=True, placeholder="—", column_config={
            "Cutoff": st.column_config.NumberColumn("Cutoff (≥)", format="%.1f"),
            "GPA points": st.column_config.NumberColumn(format="%.1f"),
            "Share": st.column_config.NumberColumn(format="%.0f%%"),
            "Highest": st.column_config.NumberColumn(format="%.1f"),
            "Lowest": st.column_config.NumberColumn(format="%.1f"),
            "Gap": st.column_config.NumberColumn(
                "Gap below", format="%.1f",
                help="Lowest total in this band minus the best total below it. The cutoff can sit "
                     "anywhere in this gap without changing anyone's grade."),
        })


# ── What-if tab ──────────────────────────────────────────────────────────────

def shift_chart(curve, cap, best, c):
    """Mean GPA against a uniform shift of every cutoff, with the cap drawn in."""
    now = curve.loc[curve["Shift"] == 0, "Mean GPA"].iloc[0]
    # The two marked points are named in a legend; text labels beside them collide with the curve
    marks = [(0.0, now, "Now", "circle")]
    if best is not None and best["Shift"] != 0:
        marks.append((best["Shift"], best["Mean GPA"], "Most generous within cap", "diamond"))

    fig = go.Figure()
    fig.add_hrect(y0=cap, y1=4.2, fillcolor=c["critical"], opacity=0.07, line_width=0, layer="below")
    fig.add_hline(y=cap, line=dict(color=c["critical"], width=1.5, dash="dash"))
    fig.add_annotation(x=1, xref="paper", xanchor="right", y=cap, yanchor="bottom", showarrow=False,
                       text=f"Cap {cap:.2f}", font=dict(color=c["ink"]))
    # "vh" steps: the mean holds until a cutoff passes the next student's total, then drops
    fig.add_trace(go.Scatter(
        x=curve["Shift"], y=curve["Mean GPA"], mode="lines", line=dict(color=c["mark"], width=2, shape="vh"),
        hovertemplate="Cutoffs %{x:+.1f} pts<br>Mean GPA %{y:.3f}<extra></extra>", showlegend=False,
    ))
    for shift, mean_gpa, name, symbol in marks:
        fig.add_trace(go.Scatter(
            x=[shift], y=[mean_gpa], mode="markers", name=name,
            marker=dict(size=12, symbol=symbol, color=c["mark"], line=dict(width=2, color=c["surface"])),
            hovertemplate=f"{name}<br>Cutoffs %{{x:+.1f}} pts<br>Mean GPA %{{y:.3f}}<extra></extra>",
        ))

    low, high = curve["Mean GPA"].min(), curve["Mean GPA"].max()
    fig.update_xaxes(title="Points added to every cutoff", zeroline=False)
    fig.update_yaxes(title="Mean GPA", range=[min(low, cap) - 0.05, max(high, cap) + 0.05])
    fig.update_layout(height=360, margin=dict(t=30, b=10, l=10, r=10),
                      legend=dict(orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom"))
    return fig


def render_what_if(graded, cutoffs, cap, max_score, curve, best):
    c = chart_colors()

    col1, col2 = st.columns((1.8, 1))
    with col1:
        st.subheader("Mean GPA if every cutoff moves together")
        # Show ±10 points around today's cutoffs, widened to include the suggestion
        center = 0.0 if best is None else best["Shift"]
        window = curve[curve["Shift"].between(min(-10, center - 3), max(10, center + 3))]
        st.plotly_chart(shift_chart(window, cap, best, c))
        st.caption("Left of zero is more generous (every cutoff lower). The line steps down each "
                   "time a cutoff moves past a student's total.")

    with col2:
        st.subheader("Most generous cutoffs within the cap")
        if best is None:
            st.warning("No uniform shift gets the mean GPA under a cap this low.")
        elif best["Shift"] == 0:
            one_lower = curve.loc[curve["Shift"] == -SHIFT_STEP, "Mean GPA"]
            st.info("Your cutoffs are already the most generous uniform setting that meets the cap."
                    + (f" Half a point lower, the mean would be {one_lower.iloc[0]:.3f}." if len(one_lower) else ""))
        else:
            shift = best["Shift"]
            suggested = {letter: min(max(cut + shift, 0.0), max_score) for letter, cut in cutoffs.items()}
            verb = "Lower" if shift < 0 else "Raise"
            st.markdown(f"{verb} every cutoff by **{abs(shift):g} points** for a mean GPA of "
                        f"**{best['Mean GPA']:.3f}**.")
            st.dataframe(pd.DataFrame({"Grade": list(cutoffs), "Now": list(cutoffs.values()),
                                       "Suggested": list(suggested.values())}),
                         hide_index=True, column_config={
                             "Now": st.column_config.NumberColumn(format="%.1f"),
                             "Suggested": st.column_config.NumberColumn(format="%.1f")})
            st.button("Use these cutoffs", type="primary", icon=":material/check:",
                      on_click=set_cutoffs, args=(suggested, max_score))

    st.subheader("Students just short of the next grade")
    margin = st.slider("Points short, at most", 0.5, 10.0, 2.0, SHIFT_STEP, width=320)
    near = graded[graded["To next grade"] <= margin].sort_values("To next grade")
    if near.empty:
        st.caption("Nobody is that close to the next grade.")
        return

    near = near.assign(**{"Next grade": near["Letter"].map(NEXT_UP)})
    st.dataframe(near[["Student", "Total", "Letter", "Next grade", "To next grade"]], hide_index=True,
                 column_config={"Letter": "Grade",
                                "Total": st.column_config.NumberColumn(format="%.1f"),
                                "To next grade": st.column_config.NumberColumn("Points short", format="%.1f")})
    bumped = graded["GPA"].copy()
    bumped.loc[near.index] = near["Next grade"].map(GPA_POINTS)
    new_mean = bumped.mean()
    verdict = "still within" if new_mean <= cap + 1e-9 else "over"
    st.caption(f"Moving all {len(near)} of them up one grade would make the mean GPA "
               f"{new_mean:.3f}, {verdict} the {cap:.2f} cap.")


# ── Score columns tab ────────────────────────────────────────────────────────

def render_columns(graded, used_cols):
    c = chart_colors()
    st.subheader("Score columns")
    stats = score_stats(graded, used_cols)
    st.dataframe(stats.assign(**{"Mean vs top": stats["Mean vs top"] * 100}), hide_index=True, placeholder="—",
                 column_config={
                     "Top score": st.column_config.NumberColumn(format="%.1f"),
                     "Mean": st.column_config.NumberColumn(format="%.2f"),
                     "Median": st.column_config.NumberColumn(format="%.1f"),
                     "Std dev": st.column_config.NumberColumn(format="%.2f"),
                     "Lowest": st.column_config.NumberColumn(format="%.1f"),
                     "Zeros": st.column_config.NumberColumn(help="Students with a 0 in this column."),
                     "Mean vs top": st.column_config.NumberColumn(format="%.0f%%",
                                                                  help="Mean as a share of the top score."),
                 })

    # Columns are out of different points (Final is 50, homeworks 8), so compare them as a share of the top score
    top = graded[used_cols].max().replace(0, float("nan"))
    long = graded.melt(id_vars=["Student"], value_vars=used_cols, var_name="Column", value_name="Score")
    long["Share of top"] = long["Score"] / long["Column"].map(top)
    fig = px.box(long, x="Column", y="Share of top", points="outliers", hover_data=["Student", "Score"],
                 color_discrete_sequence=[c["mark"]])
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Score as a share of the top score", tickformat=".0%")
    fig.update_layout(height=380, margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig)


# ── Roster tab ───────────────────────────────────────────────────────────────

def render_roster(roster, name_cols, used_cols, cutoffs):
    grades = [g for g in LETTERS + ["W"] if (roster["Letter"] == g).any()]
    picked = st.pills("Show grades", grades, selection_mode="multi", default=grades)
    columns = (name_cols or ["Student"]) + used_cols + ["Total", "Letter", "GPA", "To next grade"]
    table = roster.sort_values("Total", ascending=False)[columns]
    shown = table[table["Letter"].isin(picked)] if picked else table

    st.dataframe(shown, hide_index=True, placeholder="—", column_config={
        "Total": st.column_config.NumberColumn(format="%.1f"),
        "Letter": "Grade",
        "GPA": st.column_config.NumberColumn(format="%.1f"),
        "To next grade": st.column_config.NumberColumn("Points short", format="%.1f",
                                                       help="Points short of the next letter up."),
    })

    # Downloads hold every student, whatever the filter shows
    excel = io.BytesIO()
    with pd.ExcelWriter(excel, engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Roster", index=False)
        band_table(roster[roster["Letter"] != "W"], cutoffs).to_excel(writer, sheet_name="Grade bands", index=False)
    col1, col2, _ = st.columns((1, 1, 4))
    col1.download_button("Download Excel", excel.getvalue(), file_name="graded_roster.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         icon=":material/download:", on_click="ignore")
    col2.download_button("Download CSV", table.to_csv(index=False), file_name="graded_roster.csv",
                         mime="text/csv", icon=":material/download:", on_click="ignore")
