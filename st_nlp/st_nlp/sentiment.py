#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
from textblob import TextBlob

def render_sentiment():
    st.subheader("Sentiment Analysis")
    st.write("")
    st.write("")
    raw_text = st.text_area("Text to analyse", "Enter a text here....", height=200)
    if st.button("Evaluate"):
      if len(raw_text) == 0:
        st.warning("Enter a text...")
      else:
        blob = TextBlob(raw_text)
        st.info("Sentiment Analysis")
        st.write(blob.sentiment)
        st.write("")