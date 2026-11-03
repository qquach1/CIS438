#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Run from this folder:  streamlit run st_grader.py

import hashlib
import math

import streamlit as st

from grading import (DEFAULT_CUTOFFS, best_shift, clean_scores, find_cutoffs, grade_roster, read_sheet,
                     shift_curve, split_columns)
from sidebar import render_controls, render_source, set_cutoffs
from view import render_columns, render_distribution, render_roster, render_summary, render_what_if

st.set_page_config(page_title="Grade Cutoff Explorer", page_icon="🎓", layout="wide")

st.title("Grade Cutoff Explorer")
st.caption("Move the letter-grade cutoffs in the sidebar and watch the class mean GPA against the 3.5 cap.")


@st.cache_data
def load_sheet(data, file_name, sheet):
    return read_sheet(data, file_name, sheet)


data, file_name, sheet = render_source()
try:
    raw = load_sheet(data, file_name, sheet)
except Exception as err:  # a malformed upload shouldn't take the app down
    st.error(f"Couldn't read {file_name}: {err}")
    st.stop()

name_cols, score_cols = split_columns(raw)
if not score_cols:
    st.error(f"Couldn't find any score columns in {file_name}.")
    st.stop()
scores = clean_scores(raw, name_cols, score_cols)

# Sliders run 0-100, or further if this sheet's totals can go higher
max_score = float(max(100, math.ceil(scores[score_cols].sum(axis=1).max())))

# A new file starts from its own cutoff table (grades.xlsx has one) or from the defaults
start_cutoffs = find_cutoffs(raw) or DEFAULT_CUTOFFS
file_key = f"{hashlib.md5(data).hexdigest()}:{sheet}"
if st.session_state.get("file_key") != file_key:
    st.session_state.file_key = file_key
    set_cutoffs(start_cutoffs, max_score)

used_cols, zero_is_withdrawn, cap, cutoffs = render_controls(score_cols, max_score, start_cutoffs, file_key)
if not used_cols:
    st.warning("Pick at least one column to add into the total.")
    st.stop()

roster = grade_roster(scores, used_cols, cutoffs, zero_is_withdrawn)
graded = roster[roster["Letter"] != "W"]  # everyone who counts toward the GPA stats
if graded.empty:
    st.warning("No students left to grade.")
    st.stop()

curve = shift_curve(graded["Total"], cutoffs, max_score)
best = best_shift(curve, cap)

render_summary(graded, len(roster) - len(graded), cap, best)

tab1, tab2, tab3, tab4 = st.tabs(["Distribution", "What-if", "Score columns", "Roster"])
with tab1:
    render_distribution(graded, cutoffs, max_score)
with tab2:
    render_what_if(graded, cutoffs, cap, max_score, curve, best)
with tab3:
    render_columns(graded, used_cols)
with tab4:
    render_roster(roster, name_cols, used_cols, cutoffs)
