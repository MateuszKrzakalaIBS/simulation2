#!/bin/bash
cd /home/site/wwwroot
pip install -r requirements.txt
mkdir -p plots/interactive data_cache
streamlit run web/interactive_app.py --server.port=8000 --server.address=0.0.0.0
