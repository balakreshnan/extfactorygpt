import asyncio
from datetime import datetime
import streamlit as st
import os
import openai
from typing import List, Sequence
from factorygpt import factorygpthome
from azure.cosmos import CosmosClient, exceptions
import hashlib


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



# ----------------------
# Cosmos DB Configuration
# ----------------------
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# ----------------------
# Utility Functions
# ----------------------
def get_cosmos_client():
    return CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

def get_user(username):
    try:
        client = get_cosmos_client()
        db = client.get_database_client(DATABASE_NAME)

        # Check if database exists
        db.read()  # raises CosmosResourceNotFoundError if it doesn't exist

        container = db.get_container_client(CONTAINER_NAME)

        # Check if container exists
        container.read()

        query = f"SELECT * FROM c WHERE c.username = '{username}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return items[0] if items else None

    except exceptions.CosmosResourceNotFoundError as e:
        st.error(f"Database or container not found: {e}")
        return None
    except Exception as e:
        st.error(f"Error accessing Cosmos DB: {e}")
        return None

def create_user(username, password):
    if get_user(username):
        return False, "User already exists."
    
    client = get_cosmos_client()
    db = client.get_database_client(DATABASE_NAME)
    container = db.get_container_client(CONTAINER_NAME)

    hashed = hash_password(password)
    user_doc = {
        "id": username,
        "username": username,
        "password_hash": hashed
    }
    container.create_item(user_doc)
    return True, "User registered successfully!"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    user = get_user(username)
    if user and user.get("password_hash") == hash_password(password):
        return True
    return False

# ----------------------
# Session State Setup
# ----------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ----------------------
# Login / Register Page
# ----------------------
if not st.session_state.authenticated:
    st.title("🔐 Login or Register")
    choice = st.radio("Choose action", ["Login", "Register"])

    if choice == "Login":
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful!")
                # st.experimental_rerun()
                # Sidebar navigation
                nav_option = st.sidebar.selectbox("Navigation", ["Home", "FactoryGPT"
                                                                 , "Logout"
                                                                , "About"])

                # Display the selected page
                if nav_option == "FactoryGPT":
                    factorygpthome()
                elif nav_option == "Logout":
                    st.session_state.authenticated = False
                    st.session_state.username = ""
                    # st.experimental_rerun()
                
            else:
                st.error("Invalid credentials.")

    elif choice == "Register":
        new_username = st.text_input("Choose a Username", key="reg_user")
        new_password = st.text_input("Choose a Password", type="password", key="reg_pass")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

        if st.button("Register"):
            if new_password != confirm_password:
                st.warning("Passwords do not match.")
            elif not new_username or not new_password:
                st.warning("Username and password required.")
            else:
                success, message = create_user(new_username, new_password)
                if success:
                    st.success(message)
                    st.info("You can now log in.")
                else:
                    st.error(message)

# ----------------------
# Main App Page
# ----------------------
else:
    # Sidebar navigation
    nav_option = st.sidebar.selectbox("Navigation", ["Home", "FactoryGPT"
                                                                 , "Logout"
                                                                , "About"])

    # Display the selected page
    if nav_option == "FactoryGPT":
        factorygpthome()
    elif nav_option == "Logout":
        st.session_state.authenticated = False
        st.session_state.username = ""