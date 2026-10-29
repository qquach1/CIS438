#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import plotly.express as px

def render_view( df, graph_color ):
    # st.tabs() and st.columns() have similar syntax and both use the with notation 
    # built-in graphing functions -- st.line_chart(), st.bar_chart(), st.area_chart, st.map()
    tab1, tab2, tab3, tab4 = st.tabs([ "Histograms", "Bar Chart", "Line/Area Charts",  "Map"])
    with tab1:
        col1, col2 = st.columns( (1.5,1) ) # divide the app into 2 columns with width ratio 1.2:1
        with col1:
            fig = px.histogram( df, x=df["Statute_Text"], title="histogram based on offense category", color_discrete_sequence=[graph_color] )
            fig.update_xaxes(title_text="Offense Category")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.histogram( df, x=df["Statute_Degree"], title="histogram based on the degree of offense", color_discrete_sequence=[graph_color] )
            st.plotly_chart(fig, use_container_width=True)
    
    df_weapon_grouped = df.groupby(["Weapon_Description"]).count().iloc[:, 0] # any column other than the 1st will do since all columns contain the count
    df_weapon_grouped.name = 'count'
    with tab2:
        st.bar_chart( df_weapon_grouped, color=graph_color, x_label="weapon", y_label="count" )

    df_ym_grouped = df.groupby(df['timestamp'].dt.to_period('M')).count().iloc[:, 0]
    df_ym_grouped.index = df_ym_grouped.index.to_timestamp()
    df_ym_grouped.name = 'count'
    with tab3:
        st.line_chart( df_ym_grouped, color=graph_color, x_label="year-month", y_label="count" )
        st.area_chart( df_ym_grouped, color=graph_color, x_label="year-month", y_label="count" )
        
    with tab4:
        df_map = df.dropna(subset=["longitude", "latitude"])
        st.map( df_map.sample(n=1000, replace=True) )