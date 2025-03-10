import streamlit as st
import time
import pandas as pd
from datetime import datetime
from transformers import AutoProcessor, VisionEncoderDecoderModel
from PIL import Image
import pytesseract
import asyncio

# Handle async event loop issue
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # For Windows
    asyncio.set_event_loop(asyncio.new_event_loop())

# Load OCR model from Hugging Face with Streamlit secrets
try:
    trocr_processor = AutoProcessor.from_pretrained("microsoft/trocr-base-printed", token=st.secrets["HF_AUTH_TOKEN"])
    trocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed", token=st.secrets["HF_AUTH_TOKEN"])
except KeyError:
    st.error("Please add HF_AUTH_TOKEN to streamlit secrets.")
    trocr_processor = None
    trocr_model = None

def extract_text(image):
    try:
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        st.error(f"Error during OCR: {e}")
        return ""

def validate_data(submitted, extracted):
    discrepancies = []

    # Rule 1: If status is currently employed, no need for an end date
    if submitted['Status'] == 'Currently Employed' and extracted['End Date']:
        discrepancies.append("End date provided for currently employed status")

    # Rule 2: Month difference of 5 months is manageable
    try:
        submitted_start = datetime.strptime(submitted['Start Date'], "%Y-%m-%d")
        extracted_start = datetime.strptime(extracted['Start Date'], "%Y-%m-%d")
        submitted_end = datetime.strptime(submitted['End Date'], "%Y-%m-%d") if submitted['End Date'] else None
        extracted_end = datetime.strptime(extracted['End Date'], "%Y-%m-%d") if extracted['End Date'] else None

        if abs((submitted_start - extracted_start).days) > 150:
            discrepancies.append("Start Date mismatch beyond 5 months")
        if submitted_end and extracted_end and abs((submitted_end - extracted_end).days) > 150:
            discrepancies.append("End Date mismatch beyond 5 months")
    except ValueError:
        discrepancies.append("Date format error")

    # Rule 3: Rank validation
    valid_ranks = {"1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D", "3A", "3B", "3C", "3D", "4A", "4B", "4C", "4D"}
    if submitted['Rank'] not in valid_ranks or extracted['Rank'] not in valid_ranks:
        discrepancies.append("Invalid rank")

    # Rule 4: Designation validation
    valid_designations = {"Manager", "Assistant Manager", "Deputy Manager", "Associate", "Analyst"}
    if submitted['Designation'] not in valid_designations or extracted['Designation'] not in valid_designations:
        discrepancies.append("Invalid designation")

    # Rule 5: Service Branch validation
    valid_branches = {"Operations", "Marketing", "Sales", "Product", "HR", "Finance", "Legal"}
    if submitted['Service Branch'] not in valid_branches or extracted['Service Branch'] not in valid_branches:
        discrepancies.append("Invalid service branch")

    if not discrepancies:
        return "Completely Verified"
    elif any(cond in discrepancies for cond in ["Start Date mismatch beyond 5 months", "End Date mismatch beyond 5 months", "Invalid rank"]):
        return "Discrepancy Not Verified"
    else:
        return "Verified with Discrepancy"

# Session Management
if "session_active" not in st.session_state:
    st.session_state.session_active = False
    st.session_state.start_time = None

def start_session():
    st.session_state.session_active = True
    st.session_state.start_time = time.time()

def end_session():
    st.session_state.session_active = False
    st.session_state.start_time = None
    st.success("Session ended.")

# User Login
if not st.session_state.session_active:
    st.text_input("Username")
    st.text_input("Password", type="password")
    if st.button("Login"):
        start_session()
        st.success("Login successful! Session will expire in 5 minutes.")
else:
    st.title("Verification Fulfillment Platform")
    st.subheader("Submission Form")

    with st.form("submission_form"):
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date", value=None)
        status = st.selectbox("Status", ["Currently Employed", "Resigned", "Terminated"])
        rank = st.selectbox("Rank", ["1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D", "3A", "3B", "3C", "3D", "4A", "4B", "4C", "4D"])
        designation = st.selectbox("Designation", ["Manager", "Assistant Manager", "Deputy Manager", "Associate", "Analyst"])
        service_branch = st.selectbox("Service Branch", ["Operations", "Marketing", "Sales", "Product", "HR", "Finance", "Legal"])
        submitted = {"Start Date": str(start_date), "End Date": str(end_date), "Status": status, "Rank": rank, "Designation": designation, "Service Branch": service_branch}
        submitted_form = st.form_submit_button("Proceed")

    if submitted_form:
        st.subheader("Upload Official Documents")
        uploaded_file = st.file_uploader("Upload PDF/Image", type=["png", "jpg", "jpeg", "pdf"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            extracted_text = extract_text(image)
            # Placeholder extracted data - needs actual extraction logic
            extracted_data = {"Start Date": "2023-01-01", "End Date": "2024-01-01", "Status": "Resigned", "Rank": "1A", "Designation": "Manager", "Service Branch": "Operations"}
            st.subheader("Extracted Information")
            st.write(extracted_data)
            verification_status = validate_data(submitted, extracted_data)
            st.subheader("Verification Status")
            st.write(verification_status)

            if st.button("Close"):
                end_session()

    if st.session_state.start_time:
        elapsed_time = time.time() - st.session_state.start_time
        st.write(f"Time taken: {elapsed_time:.2f} seconds")
