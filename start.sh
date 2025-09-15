#!/bin/bash
set -e
# Start the FastAPI backend server in the background on port 7861
uvicorn src.main:app --host 0.0.0.0 --port 7861 &

# Start the Streamlit frontend in the foreground on the main port 7860
streamlit run src/app.py --server.port 7860 --server.headless true
