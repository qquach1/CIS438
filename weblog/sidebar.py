#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from datetime import date

import streamlit as st

from data_loader import LOG_PATH, use_server_clock

# Progressive filtering: all requests -> drop static files -> drop bots, each one closer to real human activity
TRAFFIC = {
    "All requests": "Everything, CSS, JS, images and crawlers included",
    "Content pages": "Leaves out CSS, JS, images and socket.io",
    "Human visitors": "Content pages, minus known crawlers",
}
NOUNS = {"All requests": "requests", "Content pages": "page requests", "Human visitors": "human page requests"}


@dataclass
class Filters:
    traffic: str
    server_clock: bool
    start: date
    end: date
    sections: list

    @property
    def noun(self):
        """What the charts count under this traffic setting, e.g. "human page requests"."""
        return NOUNS[self.traffic]

    @property
    def description(self):
        return TRAFFIC[self.traffic]

    @property
    def clock_label(self):
        return "server time" if self.server_clock else "UTC"


def render_source():
    """The log to read: weblog.txt next to this app, unless one is uploaded. Returns (bytes, file name)."""
    with st.sidebar.expander("Log file", icon=":material/description:"):
        upload = st.file_uploader("Use a different log", type=["txt", "log"],
                                  help="An Apache access log in Combined Log Format, one request per line.")
        st.caption(f"Without an upload the dashboard reads **{LOG_PATH.name}** from the app's folder.")
    if upload is not None:
        return upload.getvalue(), upload.name
    if not LOG_PATH.exists():
        st.error(f"Couldn't find {LOG_PATH.name} next to the app. Upload a log under **Log file** in the sidebar.")
        st.stop()
    return LOG_PATH.read_bytes(), LOG_PATH.name


def render_filters(box, df_all, data_key):
    """Traffic, clock, date range and sections. Widgets are keyed by file so a new upload starts fresh."""
    with box:
        st.header("Filters")
        traffic = st.radio("Traffic", list(TRAFFIC), index=2, captions=list(TRAFFIC.values()),
                           help="Sets what the Traffic, Pages, Visitors and Data tabs count. The headline "
                                "numbers and the Server health, Bots and AI tools tabs always use every request.")
        clock = st.radio("Clock", ["UTC", "Server time"], horizontal=True,
                         help="UTC matches the notebook. Server time is the clock the log was written in "
                              "(US Eastern for weblog.txt: UTC−4 in summer, UTC−5 in winter).")

        # Bounds cover both clocks so switching between them never leaves the picked dates out of range
        first = min(df_all['date'].min(), df_all['local_time'].min().date())
        last = max(df_all['date'].max(), df_all['local_time'].max().date())
        picked = st.date_input("Dates", value=(first, last), min_value=first, max_value=last,
                               key=f"dates_{data_key}", help="Pick a start and an end day, say one semester.")
        start = picked[0] if len(picked) > 0 else first
        end = picked[1] if len(picked) > 1 else last

        by_volume = df_all['section'].value_counts().index.tolist()
        sections = st.multiselect("Sections", by_volume, placeholder="All sections", key=f"sections_{data_key}",
                                  help="First part of the URL path, busiest first. Leave empty for the whole site.")
    return Filters(traffic, clock == "Server time", start, end, sections)


def apply_filters(df_all, f):
    """Clock, dates and sections -- everything except the traffic slice, which the tabs choose for themselves."""
    df = use_server_clock(df_all) if f.server_clock else df_all  # df_all is the cache's own copy
    df = df[(df['date'] >= f.start) & (df['date'] <= f.end)]
    if f.sections:
        df = df[df['section'].isin(f.sections)]
    return df


def render_dataset(box, log_name, n_parsed, skipped, f, n_view):
    """Dataset summary under the filters."""
    def day(d):
        return f"{d:%b} {d.day}, {d.year}"

    with box:
        st.divider()
        st.subheader("Dataset summary")
        unread = f" ({skipped:,} unreadable)" if skipped else ""
        st.markdown(f"**File:** `{log_name}`  \n"
                    f"**Parsed:** {n_parsed:,} lines{unread}  \n"
                    f"**Period:** {day(f.start)} – {day(f.end)}  \n"
                    f"**{f.traffic}:** {n_view:,} rows")
