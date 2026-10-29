#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import streamlit as st
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

def render_prediction( model_path, training_df ):    
    password_guess = st.text_input("Enter a Password", type="password")
    if password_guess != "cis438":
        st.stop()
    else:
        st.success("Login successful!")
        
    model_file = os.path.join(model_path, "penguins_rf.pkl")
    map_file = os.path.join(model_path, "penguins_species.pkl")
    if not os.path.isfile( model_file ) or not os.path.isfile( map_file ):
        st.write("Model files not found. Please train your model first.")
        st.stop()
        
    rf_pickle = open( model_file, "rb")
    map_pickle = open( map_file, "rb")
    rfc = pickle.load(rf_pickle)
    unique_penguin_mapping = pickle.load(map_pickle)
    rf_pickle.close()
    map_pickle.close()
        
    with st.form("user_inputs"):
        col1, col2, col3, col4, col5, col6 = st.columns( 6 )
        with col1:
            island = st.selectbox("Penguin Island", options=["Biscoe", "Dream", "Torgerson"])
        with col2:
            sex = st.selectbox("Sex", options=["Female", "Male"])
        with col3:
            bill_length = st.number_input("Bill Length (mm)", min_value=0)
        with col4:
            bill_depth = st.number_input("Bill Depth (mm)", min_value=0)
        with col5:
            flipper_length = st.number_input("Flipper Length (mm)", min_value=0)
        with col6:
            body_mass = st.number_input("Body Mass (g)", min_value=0)
        st.form_submit_button()

    island_biscoe, island_dream, island_torgerson = 0, 0, 0
    if island == "Biscoe": 
        island_biscoe = 1
    elif island == "Dream": 
        island_dream = 1
    elif island == "Torgerson": 
        island_torgerson = 1

    sex_female, sex_male = 0, 0
    if sex == "Female": 
        sex_female = 1
    elif sex == "Male": 
        sex_male = 1

    new_prediction = rfc.predict(
        [
            [
                bill_length,
                bill_depth,
                flipper_length,
                body_mass,
                island_biscoe,
                island_dream,
                island_torgerson,
                sex_female,
                sex_male,
            ]
        ]
    )
    prediction_species = unique_penguin_mapping[new_prediction][0]
    st.subheader(f"Prediction of Your Penguin's Species: {prediction_species}")    
    st.write("Below are the histograms for each continuous variable separated by penguin species. The vertical line represents the inputted value.")

    col1, col2, col3 = st.columns( 3 )
    with col1:
        fig, ax = plt.subplots()
        ax = sns.displot( x=training_df["bill_length_mm"], hue=training_df["species"] )
        plt.axvline(bill_length)
        plt.title("Bill Length by Species")
        st.pyplot(ax)
        
    with col2:
        fig, ax = plt.subplots()
        ax = sns.displot(x=training_df["bill_depth_mm"], hue=training_df["species"])
        plt.axvline(bill_depth)
        plt.title("Bill Depth by Species")
        st.pyplot(ax)
        
    with col3:
        fig, ax = plt.subplots()
        ax = sns.displot(x=training_df["flipper_length_mm"], hue=training_df["species"])
        plt.axvline(flipper_length)
        plt.title("Flipper Length by Species")
        st.pyplot(ax)