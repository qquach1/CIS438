#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import streamlit as st

from grading import GPA_POINTS, LETTERS, SHIFT_STEP, sheet_names

SAMPLE = Path(__file__).parent / "grades.xlsx"


def set_cutoffs(cutoffs, max_score):
    """Point the cutoff sliders at new values -- on a new file, on Reset, and from the What-if tab.

    Streamlit only allows this before the sliders are drawn, so it runs early in the script or as a button callback.
    """
    for letter, cut in cutoffs.items():
        st.session_state[f"cut_{letter}"] = float(min(max(cut, 0.0), max_score))


def render_source():
    """File uploader; without an upload the dashboard shows the sample workbook next to this script."""
    with st.sidebar:
        st.subheader("Data")
        upload = st.file_uploader("Grade sheet (CSV or Excel)", type=["csv", "xlsx"],
                                  help="One row per student and one column per graded item. "
                                       "Letter, Grade and Total columns are ignored and recomputed.")
        if upload is None:
            data, file_name = SAMPLE.read_bytes(), SAMPLE.name
            st.caption(f"Showing the sample workbook, **{SAMPLE.name}**.")
        else:
            data, file_name = upload.getvalue(), upload.name

        try:
            sheets = sheet_names(data, file_name)
        except Exception as err:  # not a real Excel file
            st.error(f"Couldn't open {file_name}: {err}")
            st.stop()
        sheet = st.selectbox("Worksheet", sheets) if len(sheets) > 1 else 0
    return data, file_name, sheet


def render_controls(score_cols, max_score, start_cutoffs, file_key):
    """GPA cap, cutoff sliders and options. Returns everything the dashboard needs to grade."""
    with st.sidebar:
        st.subheader("Policy")
        cap = st.number_input("Mean GPA cap", 0.0, 4.0, 3.5, 0.05, format="%.2f",
                              help="Simon caps the mean GPA of a course at 3.5.")

        st.subheader("Cutoffs")
        st.caption("Lowest total that earns each grade. Anything under the C cutoff is an F.")
        # The slider values live in st.session_state (keys cut_A, cut_A-, ...) so buttons can move them
        cutoffs = {letter: st.slider(letter, 0.0, max_score, step=SHIFT_STEP, key=f"cut_{letter}")
                   for letter in LETTERS[:-1]}
        st.button("Reset cutoffs", icon=":material/restart_alt:",
                  on_click=set_cutoffs, args=(start_cutoffs, max_score))
        values = list(cutoffs.values())
        if any(higher <= lower for higher, lower in zip(values, values[1:])):
            st.warning("Cutoffs should fall from A to C. As set, some grades can't be earned.")

        st.subheader("Options")
        # Keyed by file so a new upload starts with all of its columns selected
        used_cols = st.multiselect("Columns added into the total", score_cols, default=score_cols,
                                   key=f"cols_{file_key}")
        zero_is_withdrawn = st.toggle("Treat all-zero students as withdrawn",
                                      help="The workbook counts them as an F (0.0) in the mean. "
                                           "Turn this on to leave them out of every statistic.")

        with st.expander("How grades are computed"):
            scale = " · ".join(f"{letter} {points:.1f}" for letter, points in GPA_POINTS.items())
            st.markdown(f"""
- **Total** is the sum of the selected columns (blanks count as 0).
- **Grade** is the highest letter whose cutoff the total reaches.
- **GPA points:** {scale}
- **Mean GPA** averages those points over every graded student, F's included.
""")
    return used_cols, zero_is_withdrawn, cap, cutoffs
