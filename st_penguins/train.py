#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import streamlit as st
import altair as alt

import pickle

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from scipy import stats

def render_train( data_path, model_path ):
    penguin_file = st.file_uploader('')
    if penguin_file is not None: 
        df = pd.read_csv( penguin_file )
    else: 
        df = pd.read_csv( data_path )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Visualization")
        st.markdown("This is a scatterplot of Palmer's Penguins dataset. You may also upload your local Penguins CSV.")
        selected_x_var = st.selectbox( "What do you want the x variable to be?",
            ["bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"],
        )
        selected_y_var = st.selectbox("What about the y?",
            ["bill_depth_mm", "bill_length_mm", "flipper_length_mm", "body_mass_g"],
        )

        alt_chart = (
            alt.Chart(df, title="Scatterplot of Palmer's Penguins")
            .mark_circle()
            .encode( x=selected_x_var, y=selected_y_var, color="species" )
            .interactive()
        )
        st.altair_chart( alt_chart, use_container_width=True )
        df['bill_length_mm'].corr( df['bill_depth_mm'] )
        stats.pearsonr(df['bill_length_mm'], df['bill_depth_mm'])
    
    with col2:
        st.subheader("Penguin Species Prediction")
        st.write("Train a random forest model using 6 inputs.")
        fig_path = os.path.join( model_path, "penguins_features.png" )
        if st.button("Train"):            
            df.dropna(inplace=True)
            target = df["species"]
            features = df[ ["island", "bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g", "sex"] ]
            features = pd.get_dummies(features) # Convert each categorical variable into dummies. Non-categorical variables are unaltered.
            features.iloc[0] # check the first row
            rfc = train( target=target, features=features, model_path=model_path )
            st.write("Features ranked by relative importance") 
            fig, ax = plt.subplots()
            ax = sns.barplot( x=rfc.feature_importances_, y=features.columns )
            plt.title("Which features are the most important for species prediction?")
            plt.xlabel("Importance")
            plt.ylabel("Feature")
            plt.tight_layout()            
            fig.savefig( fig_path )
            st.image( fig_path )
        elif os.path.isfile( fig_path ):
            st.image( fig_path )
        
    return df
        

def train( target, features, model_path ):    
    target, uniques = pd.factorize(target) # Encode species as an enumerated type or categorical variable.    
    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=0.8)
    rfc = RandomForestClassifier(random_state=15)
    rfc.fit( x_train.values, y_train )
    y_pred = rfc.predict(x_test.values)
    score = accuracy_score(y_pred, y_test)
    print("Accuracy score: {x:.2f}%".format(x=score*100))
    rf_pickle = open( os.path.join(model_path, "penguins_rf.pkl"), "wb")
    pickle.dump(rfc, rf_pickle)
    rf_pickle.close()
    output_pickle = open( os.path.join(model_path, "penguins_species.pkl"), "wb")
    pickle.dump(uniques, output_pickle)
    output_pickle.close()
    return rfc    