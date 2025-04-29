# login.py
import streamlit as st

def require_login():
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        st.warning("🚫 You must be logged in to access this page.")
        st.stop()  # Immediately halts page execution
