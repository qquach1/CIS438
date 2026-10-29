#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import streamlit as st
import pandas as pd

from sidebar import render_sidebar
from view import render_view
from edit import render_edit

data_path = f'{os.getenv("HOME")}/Data/csv/crime.csv'

st.set_page_config(layout="wide") # default: centered page layout

st.title("Rochester Crime Data")
st.header("Crime Data from RPD") # st.header() uses a smaller font than st.title()

df = pd.read_csv( data_path )
df["timestamp"] = pd.to_datetime( df["timestamp"] ) # convert to pandas datetime object
df["date"] = df["timestamp"].dt.date

graph_color, choice, dff = render_sidebar( df )

if choice == 'View':
    render_view( dff, graph_color )
elif choice == 'Edit':
    render_edit( data_path )