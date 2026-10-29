import streamlit as st
import matplotlib
matplotlib.use("Agg")

from css import THEMES, build_css
from sidebar import render_sidebar
from analysis import render_analysis
from translation import render_translation
from sentiment import render_sentiment

#%%

st.set_page_config (page_title="Text Analyzer", page_icon="👍", layout="centered", initial_sidebar_state="expanded" )

# ── Hero banner ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">CIS 438 &mdash; In-Class Exercise</div>
    <h1>NLP <span>Web App</span></h1>
    <div class="hero-sub">
        Lexical Analytics; Sentiment Analysis; Translation; and more!
    </div>
</div>
""", unsafe_allow_html=True)

if "theme" not in st.session_state:
    st.session_state.theme = "light"
T = THEMES[st.session_state.theme]
is_dark = st.session_state.theme == "dark"
# Use custom CSS at the start of the app to apply the theme (colors, fonts, card styles) before rendering any content.
st.markdown(build_css(T, is_dark), unsafe_allow_html=True)

choice = render_sidebar()

# ── Dashboard tabs ───────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs( ["Lexical Analysis", "Sentiment Analysis", "Translation", "About"] )

with tab1:
    render_analysis()

with tab2:
    render_sentiment()

with tab3:
    render_translation()   
    
with tab4:
    st.markdown(""" ### About this app
    In addition to **Streamlit**, the following packages are needed:
    - wordcloud
    - deep_translator
    - textblob
    - neattext
    - *spacy*  
    
    To install, run the following:
    - `pip install wordcloud deep_translator textblob neattext spacy`
    - `python -m spacy download en_core_web_sm`
    """)    