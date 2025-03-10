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
except ImportError as e:
    st.error(f"ImportError: {e}. Ensure transformers library is correctly installed and updated.")
    trocr_processor = None
    trocr_model = None
except Exception as e:
    st.error(f"An unexpected error occurred during model loading: {e}")
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
