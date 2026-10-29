#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="theme-toggle-label">Appearance</div>', unsafe_allow_html=True)
        theme_choice = st.toggle("Light Mode", value=(st.session_state.theme == "light"), key="theme_toggle")
        new_theme = "light" if theme_choice else "dark"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()