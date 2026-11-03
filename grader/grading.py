#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grading rules from the Final_Grade sheet in grades.xlsx, as plain pandas (no Streamlit here)."""

import io

import numpy as np
import pandas as pd

# Simon's letter grades from best to worst and the GPA points each earns (M5:M11 in the workbook)
LETTERS = ["A", "A-", "B+", "B", "B-", "C", "F"]
GPA_POINTS = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C": 2.0, "F": 0.0}
NEXT_UP = {LETTERS[i]: LETTERS[i - 1] for i in range(1, len(LETTERS))}  # "A-" -> "A", ..., "F" -> "C"

# Lowest total that earns each letter (F5:F10 in the workbook); anything under the C cutoff is an F
DEFAULT_CUTOFFS = {"A": 98.0, "A-": 90.0, "B+": 80.0, "B": 60.0, "B-": 50.0, "C": 40.0}

# Columns the workbook derives from the scores -- recomputed here, never added into the total
DERIVED_COLUMNS = {"letter", "grade", "total", "gpa", "id", "student id"}

SHIFT_STEP = 0.5  # the cutoff sliders move in half points


# ── Reading a grade sheet ────────────────────────────────────────────────────

def is_csv(file_name):
    return file_name.lower().endswith(".csv")


def sheet_names(data, file_name):
    """Worksheet names in an Excel file; a CSV has none."""
    if is_csv(file_name):
        return []
    with pd.ExcelFile(io.BytesIO(data)) as book:
        return book.sheet_names


def read_sheet(data, file_name, sheet=0):
    """Read an uploaded CSV or Excel file into a DataFrame."""
    if is_csv(file_name):
        return pd.read_csv(io.BytesIO(data))
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet)


def split_columns(raw):
    """Sort a sheet's columns into name columns and score columns.

    Columns without a header are skipped -- that's where the workbook keeps its summary
    table -- along with the columns it calculates itself (Letter, Grade, Total).
    """
    name_cols, score_cols = [], []
    for col in raw.columns:
        values = raw[col].dropna()
        label = str(col).strip().lower()
        if values.empty or label.startswith("unnamed") or label in DERIVED_COLUMNS:
            continue
        if pd.to_numeric(values, errors="coerce").notna().mean() >= 0.9:
            score_cols.append(col)
        else:
            name_cols.append(col)
    return name_cols, score_cols


def find_cutoffs(raw):
    """Read the cutoff table from a workbook laid out like grades.xlsx, or return None.

    That table lists each letter once (G5:G11) with its cutoff just to the left (F5:F11).
    """
    columns = list(raw.columns)
    for left, right in zip(columns, columns[1:]):
        letters = raw[right].astype(str).str.strip()
        rows = letters[letters.isin(list(DEFAULT_CUTOFFS))]
        if len(rows) == len(DEFAULT_CUTOFFS) and rows.is_unique:
            values = pd.to_numeric(raw.loc[rows.index, left], errors="coerce")
            if values.notna().all():
                return {letter: float(value) for letter, value in zip(rows, values)}
    return None


def student_names(scores, name_cols):
    """A display name per row: "First Last" when the sheet has both columns."""
    if not name_cols:
        return pd.Series([f"Student {i + 1}" for i in range(len(scores))], index=scores.index)
    text = scores[name_cols].fillna("").astype(str)
    first = next((c for c in name_cols if "first" in str(c).lower()), None)
    last = next((c for c in name_cols if "last" in str(c).lower()), None)
    if first is not None and last is not None:
        return (text[first] + " " + text[last]).str.strip()
    return text.agg(" ".join, axis=1).str.strip()


def clean_scores(raw, name_cols, score_cols):
    """Names plus numeric scores, one row per student (blank rows dropped)."""
    scores = raw[name_cols + score_cols].copy()
    scores[score_cols] = scores[score_cols].apply(pd.to_numeric, errors="coerce")
    scores = scores.dropna(subset=score_cols, how="all").reset_index(drop=True)
    scores["Student"] = student_names(scores, name_cols)
    return scores


# ── Grading ──────────────────────────────────────────────────────────────────

def _clears(totals, cutoffs):
    """One True/False array per passing letter: did each total reach that cutoff?"""
    totals = np.asarray(totals, dtype=float)
    return [totals >= cutoffs[letter] for letter in LETTERS[:-1]]


def letter_grades(totals, cutoffs):
    """Letter for each total: the first cutoff it clears, same as the workbook's nested IF."""
    return np.select(_clears(totals, cutoffs), LETTERS[:-1], default="F")


def gpa_points(totals, cutoffs):
    """GPA points for each total -- the workbook's Grade column."""
    points = [GPA_POINTS[letter] for letter in LETTERS[:-1]]
    return np.select(_clears(totals, cutoffs), points, default=GPA_POINTS["F"])


def grade_roster(scores, used_cols, cutoffs, zero_is_withdrawn=False):
    """Add each student's Total, Letter and GPA points, plus how far they were from the next grade."""
    roster = scores.copy()
    roster["Total"] = roster[used_cols].sum(axis=1)  # blanks count as 0, like Excel's SUM
    roster["Letter"] = letter_grades(roster["Total"], cutoffs)
    roster["GPA"] = roster["Letter"].map(GPA_POINTS)
    if zero_is_withdrawn:
        withdrawn = roster["Total"] == 0
        roster.loc[withdrawn, "Letter"] = "W"
        roster.loc[withdrawn, "GPA"] = np.nan

    # Points short of the next letter up (blank for an A or a withdrawal)
    next_cutoff = {letter: cutoffs[up] for letter, up in NEXT_UP.items()}
    roster["To next grade"] = roster["Letter"].map(next_cutoff) - roster["Total"]
    return roster


# ── Summaries ────────────────────────────────────────────────────────────────

def band_table(graded, cutoffs):
    """One row per letter, like the Highest / Lowest / Gap / Count / Percentage block in the workbook."""
    rows = []
    for i, letter in enumerate(LETTERS):
        band = graded.loc[graded["Letter"] == letter, "Total"]
        below = graded.loc[graded["Letter"].isin(LETTERS[i + 1:]), "Total"]
        rows.append({
            "Grade": letter,
            "Cutoff": cutoffs.get(letter, np.nan),
            "GPA points": GPA_POINTS[letter],
            "Students": len(band),
            "Share": len(band) / len(graded),
            "Highest": band.max(),
            "Lowest": band.min(),
            # Empty stretch between this band's lowest total and the best total below it
            "Gap": band.min() - below.max(),
        })
    return pd.DataFrame(rows)


def shift_curve(totals, cutoffs, max_score):
    """Mean GPA if every cutoff moved by the same amount, in half-point steps across the whole scale."""
    n = int(np.ceil(max_score / SHIFT_STEP))
    shifts = np.arange(-n, n + 1) * SHIFT_STEP
    means = []
    for shift in shifts:
        moved = {letter: min(max(cut + shift, 0.0), max_score) for letter, cut in cutoffs.items()}
        means.append(gpa_points(totals, moved).mean())
    return pd.DataFrame({"Shift": shifts, "Mean GPA": means})


def best_shift(curve, cap):
    """The most generous uniform shift that keeps the mean GPA at or under the cap, or None.

    Raising cutoffs can only lower grades, so this is the first shift on the curve that meets the cap.
    """
    meets_cap = curve[curve["Mean GPA"] <= cap + 1e-9]
    return None if meets_cap.empty else meets_cap.iloc[0]


def score_stats(graded, used_cols):
    """Summary statistics for each column that goes into the total."""
    scores = graded[used_cols]
    stats = pd.DataFrame({
        "Top score": scores.max(),
        "Mean": scores.mean(),
        "Median": scores.median(),
        "Std dev": scores.std(),
        "Lowest": scores.min(),
        "Zeros": (scores == 0).sum(),
    })
    stats["Mean vs top"] = stats["Mean"] / stats["Top score"].replace(0, np.nan)
    return stats.rename_axis("Column").reset_index()
