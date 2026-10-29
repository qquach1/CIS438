#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import streamlit as st
from wordcloud import WordCloud
import neattext as nt
import spacy

@st.cache_data
def text_analyzer(text):    
    nlp = spacy.load('en_core_web_sm') # import English library    
    doc = nlp(text) # create an nlp object    
    allData = [('"Token":{},\n"Lemma":{}'.format(token.text, token.lemma_)) for token in doc] #extract tokens and lemmas
    return allData

def render_analysis():
    st.subheader("Text Analysis")
    st.write("")
    raw_text = st.text_area("Write something", "Enter a text in English...", height=200)
    if st.button("Analyze"):
      if len(raw_text) == 0:
        st.warning("Enter a text...")
      else:       
        processed_text_mid = str(nt.TextFrame(raw_text).remove_stopwords())
        processed_text_mid = str(nt.TextFrame(processed_text_mid).remove_puncts())
        processed_text_fin = str(nt.TextFrame(processed_text_mid).remove_special_characters())
        word_desc = nt.TextFrame(raw_text).word_stats()
        num_unique_words = nt.TextFrame(processed_text_fin).nunique()
        cards_html = '<div class="metric-grid">'
        for label, val in [("Num of Characters", f"{word_desc['Length of Text']:,}"), ("Num of Vowels", f"{word_desc['Num of Vowels']:,}"),
            ("Num of Consonants", f"{word_desc['Num of Consonants']:,}"), ("Num of Stopwords", f"{word_desc['Num of Stopwords']:,}"), ("Num of Unique Words", f"{num_unique_words:,}")]:
            cards_html += f'<div class="m-card"><div class="m-val">{val}</div><div class="m-label">{label}</div></div>'
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)        
          
        col1, col2 = st.columns(2)
        with col1:          

          with st.expander("Stopwords"):
            st.success("Stop Words List")
            stop_w = nt.TextExtractor(raw_text).extract_stopwords()
            st.error(stop_w)
            
          with st.expander("Tokens & Lemmas"):
            st.write("T&K")            
            tandl = text_analyzer(processed_text_fin)
            st.json(tandl)

        with col2:
          with st.expander("Processed Text"):
            st.success("Stopwords Excluded Text")
            processed_text = str(nt.TextFrame(raw_text).remove_stopwords())
            st.write(processed_text)

          with st.expander("Plot Wordcloud"):
            st.success("Wordcloud")
            wordcloud = WordCloud().generate(processed_text)
            fig = plt.figure(1, figsize=(20,10))
            plt.imshow(wordcloud, interpolation = 'bilinear')
            plt.axis('off')
            st.pyplot(fig)

        
        