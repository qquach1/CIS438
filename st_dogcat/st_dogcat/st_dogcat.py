"""
An image classification app that distinguishes dogs from cats, using a convolutional neural network. 
"""

import streamlit as st
import os
from PIL import Image,ImageEnhance
import model # model, which identifies the file to be loaded, becomes a variable assigned to the loaded module
from css import THEMES, build_css

#%%
st.set_page_config(page_title="Image Analytics", page_icon="👍", layout='centered', initial_sidebar_state='auto')

st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">CIS 438 &mdash; In-Class Exercise</div>
    <h1>Image <span>Analytics</span></h1>
    <div class="hero-sub">
        Image enhancement, classification, and more!
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

image_file = st.sidebar.file_uploader("Upload an image (jpg, png or jpeg) of dog or cat", type=['jpg','png','jpeg'])
if image_file is None:
    image_file = f'{os.getenv("HOME")}/Data/img/cat.jpg'

original_image = Image.open(image_file)    

if st.sidebar.button("Image Preview"):
    st.sidebar.image(original_image,width=300)
activities = ["Image Enhancement","Image Classification"]
choice = st.sidebar.selectbox("Select Activty",activities)
if choice == 'Image Enhancement':    
    enhance_type = st.sidebar.radio("Enhance Type", ["Original", "Contrast", "Brightness"])
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if enhance_type == "Contrast":
            c_rate = st.slider("Contrast", 0.5, 5.0)
            enhancer = ImageEnhance.Contrast(original_image)
            img_output = enhancer.enhance(c_rate)
            st.image( img_output )
        elif enhance_type == "Brightness":
            c_rate = st.slider("Brightness", 0.5, 5.0)
            enhancer = ImageEnhance.Brightness(original_image)
            img_output = enhancer.enhance(c_rate)
            st.image(img_output)
        else:
            st.image(original_image)
    
elif choice == 'Image Classification':
    st.sidebar.warning("Caution: I can only tell dogs from cats.")
    st.image(original_image)
    if st.sidebar.button("Classify"):        
        img = original_image.convert("RGB")
        dog = model.predict( img )
        if dog > 0.5:
            st.success(f"It's a dog! Prob(dog=1)={dog:.2f}")
        else:
            st.success(f"It's a cat! Prob(dog=1)={dog:.2f}")
        
if st.sidebar.button("About the Author"):
    st.sidebar.subheader("Cat or Dog")
    st.sidebar.markdown("by [Huaxia Rui](https://simonbb.com)")
    st.sidebar.markdown("[huaxia.rui@simon.rochester.edu](mailto:huaxia.rui@simon.rochester.edu)")
    st.sidebar.text("All Rights Reserved (2026)")