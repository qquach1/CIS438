import pandas as pd
import streamlit as st

def render_edit( data_path ):
    st.write("Edit the data and save to a new file!")

    df = pd.read_csv( data_path )
    df = df.dropna(subset=["longitude", "latitude"])
         
    edited_df = st.data_editor( df )
    df.loc[edited_df.index] = edited_df

    if st.button("Save data and overwrite"):
        df.to_csv( data_path, index=False)
        st.write("Saved!")