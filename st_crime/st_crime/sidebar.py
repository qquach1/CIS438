#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st

def render_sidebar( df ):
    with st.sidebar:
        graph_color = st.color_picker("Graph Colors")
        activity = ["View", "Edit"]
        choice = st.selectbox("Menu", activity)
        st.markdown("---")
        st.markdown("""
        <div style="font-family:var(--font-display); font-size:1.3rem; color:var(--text); font-weight:600; margin-bottom:1.2rem;">
            Filters
        </div>
        """, unsafe_allow_html=True)

        # Date range derived from actual data bounds — lets users focus on specific periods (e.g., a single semester)
        min_date = df['date'].min()
        max_date = df['date'].max()
        date_range = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        # Progressive filtering: All → remove static files → remove bots = increasingly focused on real human activity
        geo_section = st.radio("Geo Section", ["All", "Lake", "Goodman", "Clinton", "Genesee"], index=0)
        statute_filter = st.multiselect("Statute", sorted(df['Statute_Text'].unique()), default=[])              
    
    if geo_section == "All":
        dff = df.copy()
    else:
        dff = df[ df['Geo_Section']==geo_section ]

    if len(date_range) == 2:
        dff = dff[(dff['date'] >= date_range[0]) & (dff['date'] <= date_range[1])]
    if statute_filter:
        dff = dff[dff['Statute_Text'].isin(statute_filter)]
        
    with st.sidebar:
        st.markdown("---")
        st.markdown('<div style="font-family:var(--font-mono);font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase;color:var(--primary);margin-bottom:0.6rem;">Dataset Summary</div>', unsafe_allow_html=True)
        if len(date_range) == 2:
            st.markdown(f"**Period:** `{date_range[0]}` to `{date_range[1]}`")
        else:
            st.markdown(f"**Period:** `{min_date}` to `{max_date}`")
        st.markdown(f"**Entries:** `{len(dff):,}`") 
        
    return graph_color, choice, dff