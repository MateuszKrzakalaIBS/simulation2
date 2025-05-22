#!/bin/bash

# Install required packages for Streamlit Cloud deployment
pip install -r requirements.txt

# Create necessary directories
mkdir -p plots/interactive data_cache

# Set environment variables
export STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true
