import asyncio
from datetime import datetime
import streamlit as st
import os
import openai
from typing import List, Sequence
from factorygpt import factorygpthome


# Set page size
st.set_page_config(
    page_title="Gen AI Application Validation",
    page_icon=":rocket:",
    layout="wide",  # or "centered"
    initial_sidebar_state="expanded"  # or "collapsed"
)

# Load your CSS file
def load_css(file_path):
    with open(file_path, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Call the function to load the CSS
load_css("styles.css")

# Sidebar navigation
nav_option = st.sidebar.selectbox("Navigation", ["Home", 
                                                 "FactoryGPT"
                                                 , "About"])

# Display the selected page
if nav_option == "FactoryGPT":
    factorygpthome()