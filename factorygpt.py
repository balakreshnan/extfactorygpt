from datetime import datetime
import streamlit as st
import openai
import os
from PyPDF2 import PdfReader
import json
from mfgdata import extractmfgresults, extracttop5questions, askwithpdf, rootcauseanalysis, supplychainassistant, productionplanning
import datetime
from azure.cosmos import CosmosClient, exceptions

# from login import require_login

# require_login()

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

# Helper function to read text files
def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Helper function to read PDF files
def read_pdf_file(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

@st.cache_data
# Function to fetch content of the source
def fetch_source_content(file_name):
    # file_path = os.path.join('sources', file_name)
    file_path = file_name
    if file_name.endswith('.txt'):
        return read_text_file(file_path)
    elif file_name.endswith('.pdf'):
        return read_pdf_file(file_path)
    return "Unsupported file format."

# Fetch user's access record
def get_user_indexes(email, company_id):

    # Initialize Cosmos client
    CONTAINER_NAME = "indexcol"
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)

    query = f"SELECT * FROM c WHERE c.email = '{email}'"
    print('query: ', query)
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    if not items:
        return []

    user_doc = items[0]
    print("user doc", user_doc)
    # if user_doc["role"] == "admin":
    #     # For admins, get all unique indexes in this company (example logic)
    #     index_query = f"""
    #     SELECT DISTINCT VALUE idx FROM c
    #     JOIN idx IN c.indexes
    #     WHERE c.companyId = @companyId AND c.type = "userAccess"
    #     """
    #     idx_items = list(container.query_items(
    #         query=index_query,
    #         parameters=[{"name": "@companyId", "value": company_id}],
    #         partition_key=company_id
    #     ))
    #     return sorted(set(idx_items))
    # else:
    #     return sorted(user_doc.get("indexes", []))
    return sorted(user_doc.get("indexes", []))

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize chat history in session state
if "chat_history_pdf" not in st.session_state:
    st.session_state.chat_history_pdf = []

# Initialize session state
if "uploaddata" not in st.session_state:
    st.session_state.uploaddata = None

MOCK_COMPANY_ID = "companyA"

# Streamlit App
def factorygpthome():
    
    tab1, tab2 = st.tabs(["Manufacturing GPT", "Source"])
    with tab1:
        st.header("Manufacturing GPT")        

        print('Email: ', st.session_state.email)
        if st.session_state.email:
            user_indexes = get_user_indexes(st.session_state.email, MOCK_COMPANY_ID)
            if user_indexes:
                selected_index = st.selectbox("Choose an Topic:", user_indexes)
                st.success(f"You selected: {selected_index}")
                # Display top 5 questions
                with st.spinner("Loading top 5 questions for {selected_index} ......"):
                    top5questions = extracttop5questions(selected_index)
                    st.markdown(top5questions, unsafe_allow_html=True)
            else:
                st.warning("No indexes available or user not authorized.")

        if prompt := st.chat_input("what are the personal protection i should consider in manufacturing?", key="chat1"):
            with st.spinner("Processing..."):
                # Call the extractproductinfo function
                #st.write("Searching for the query: ", prompt)
                if user_indexes:
                    st.chat_message("user").markdown(prompt, unsafe_allow_html=True)
                    st.session_state.chat_history.append({"role": "user", "message": prompt})
                    starttime = datetime.datetime.now()
                    rfttopics = extractmfgresults(prompt, selected_index)
                    endtime = datetime.datetime.now()

                    #st.markdown(f"Time taken to process: {endtime - starttime}", unsafe_allow_html=True)
                    rfttopics += f"\n Time taken to process: {endtime - starttime}"
                    st.session_state.chat_history.append({"role": "assistant", "message": rfttopics})
                    st.chat_message("assistant").markdown(rfttopics, unsafe_allow_html=True)

                    # Keep only the last 10 messages
                    if len(st.session_state.chat_history) > 20:  # 10 user + 10 assistant
                        st.session_state.chat_history = st.session_state.chat_history[-20:]
    with tab2:
        st.header("Upload your own source")
        uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
        with st.spinner("Loading..."):
            if uploaded_file and st.session_state.uploaddata is None:
                # Save the uploaded file to the 'sources' directory
                # file_path = os.path.join('sources', uploaded_file.name)
                file_path = uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("File uploaded successfully!")
                # Fetch and display the content of the uploaded file
                # content = fetch_source_content(uploaded_file.name)                
                st.session_state.data = fetch_source_content(uploaded_file.name)

        query = st.text_input("Ask a question about the uploaded file")
        if st.button("Delete"):
            if uploaded_file is not None:
                # Delete the uploaded file
                # file_path = os.path.join('sources', uploaded_file.name)
                file_path = uploaded_file.name
                if os.path.exists(file_path):
                    os.remove(file_path)
                    uploaded_file.close()
                    st.session_state.uploaded_file = None
                    st.success("File deleted successfully!")
                else:
                    st.error("File not found.") 
        if st.button("Ask"):
            with st.spinner("Processing..."):
                if st.session_state.data is not None:
                    #st.text_area("Content of the uploaded file", value=content, height=300)
                    pdfresult = askwithpdf(query, st.session_state.data)
                    st.markdown(pdfresult, unsafe_allow_html=True)