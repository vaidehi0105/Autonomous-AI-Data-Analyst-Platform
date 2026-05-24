import streamlit as st

import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
)

from app.agents.ingestion_agent import IngestionAgent

st.title("Autonomous AI Analytics Platform")

uploaded_file = st.file_uploader(
    "Upload CSV File",
    type=["csv"]
)

if uploaded_file:

    agent = IngestionAgent()

    result = agent.ingest_csv(uploaded_file)

    st.success("Dataset Uploaded Successfully")

    st.write(result)