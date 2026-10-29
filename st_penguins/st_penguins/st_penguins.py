import os
import streamlit as st

from train import render_train
from predict import render_prediction
from css import THEMES, build_css

#%%

st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">CIS 438 &mdash; In-Class Exercise</div>
    <h1>Penguins <span>Species</span></h1>
    <div class="hero-sub">
        Visualization and Prediction
    </div>
</div>
""", unsafe_allow_html=True)

if "theme" not in st.session_state:
    st.session_state.theme = "light"
T = THEMES[st.session_state.theme]
is_dark = st.session_state.theme == "dark"
# Use custom CSS at the start of the app to apply the theme (colors, fonts, card styles) before rendering any content.
st.markdown(build_css(T, is_dark), unsafe_allow_html=True)

#%%

data_dir = f'{os.getenv("HOME")}/Data'
data_path = os.path.join( data_dir, 'csv/penguins.csv' )
model_path = os.path.join( data_dir, 'models/penguins/')

tab1, tab2 = st.tabs( ["Visualization/Training", "Prediction"] )

with tab1:
    df = render_train( data_path, model_path )
with tab2:
    render_prediction( model_path=model_path, training_df = df )