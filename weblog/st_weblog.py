#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Run from this folder:  streamlit run st_weblog.py

import streamlit as st

from data_loader import load_data, split_traffic
from sidebar import apply_filters, render_dataset, render_filters, render_source
from view import (render_ai_tools, render_bots, render_data, render_kpis, render_pages, render_server,
                  render_traffic, render_visitors)

st.set_page_config(page_title="WebLog Observatory", page_icon="🔭", layout="wide")
st.title("WebLog Observatory")

# Sidebar order: filters, then the dataset summary, then the log-file picker (which has to run first)
filters_box = st.sidebar.container()
summary_box = st.sidebar.container()
log_bytes, log_name = render_source()

try:
    df_all, skipped = load_data(log_bytes)
except Exception as err:  # a file that isn't an access log shouldn't take the app down
    st.error(f"Couldn't read {log_name}: {err}")
    st.stop()
if df_all.empty:
    st.error(f"No line in {log_name} looks like an Apache access log entry.")
    st.stop()

f = render_filters(filters_box, df_all, data_key=f"{log_name}:{len(log_bytes)}")
df = apply_filters(df_all, f)                # notebook section 6: df, then its two slices
df_pages, df_humans = split_traffic(df)
view = {"All requests": df, "Content pages": df_pages, "Human visitors": df_humans}[f.traffic]
render_dataset(summary_box, log_name, len(df_all), skipped, f, len(view))

internal = df_all.loc[df_all['referer_type'] == 'Internal', 'referer_host']
site = internal.mode().iloc[0] if not internal.empty else "the site"
st.caption(f"Who visits **{site}**, what they read, and how the server answers, read from {log_name}. "
           "The numbers below count every request in the selected dates.")

if df.empty:
    st.warning("No requests match these filters. Widen the dates or clear the sections in the sidebar.")
    st.stop()

render_kpis(df)

# Only the open tab runs, so switching tabs stays quick on a big log
tabs = st.tabs(["Traffic", "Pages", "Visitors", "Server health", "Bots", "AI tools", "Data"],
               key="tab", on_change="rerun")
pages = [
    lambda: render_traffic(view, f),
    lambda: render_pages(view, f),
    lambda: render_visitors(view, f, geo_ok=df_all['latitude'].notna().any()),
    lambda: render_server(df),
    lambda: render_bots(df, df_pages),
    lambda: render_ai_tools(df, site),
    lambda: render_data(view, f),
]
for tab, render in zip(tabs, pages):
    if tab.open:
        with tab:
            render()
