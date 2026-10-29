#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import streamlit as st
import pandas as pd
import plotly.express as px

data_path = f'{os.getenv("HOME")}/Data/csv/crime.csv'

st.set_page_config(layout="wide") # default: centered page layout

st.title("Rochester Crime Data")
st.header("Crime Data from RPD") # st.header() uses a smaller font than st.title()

graph_color = st.sidebar.color_picker("Graph Colors")

df = pd.read_csv( data_path )
df["date"] = pd.to_datetime(df["timestamp"]) # convert to pandas datetime object

# st.tabs() and st.columns() have similar syntax and both use the with notation 
tab1, tab2, tab3 = st.tabs([ "Histograms", "Bar Chart", "Map"])
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
    
with tab3:
    df_map = df.dropna(subset=["longitude", "latitude"])
    st.map( df_map.sample(n=1000, replace=True) )