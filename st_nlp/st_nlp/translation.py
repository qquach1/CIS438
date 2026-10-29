#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
from deep_translator import GoogleTranslator

def render_translation():
    st.subheader("Translation")
    st.write("")
    st.write("")
    raw_text = st.text_area("Original Text", "Write something to be translated...", height=200)
    if len(raw_text) < 3:
      st.warning("Please provide a text with at least 3 characters...")
    else:
      target_lang = st.selectbox("Target Language", ["German", "Spanish", "French", "Italian"])
      if target_lang == "German":
        target_lang = "de"
      elif target_lang == "Spanish":
        target_lang = "es"
      elif target_lang == "French":
        target_lang = "fr"      
      else:
        target_lang = "it" 
      
      if st.button("Translate"):
        translator = GoogleTranslator(source='auto', target=target_lang)  # set source and target languages
        translated_text = translator.translate(raw_text)
        st.write(translated_text)