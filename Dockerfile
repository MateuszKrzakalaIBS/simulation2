FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Create necessary directories
RUN mkdir -p plots/interactive data_cache

# Expose port for Streamlit
EXPOSE 8501

# Set environment variable to disable file watcher
ENV STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

# Command to run the application
CMD ["streamlit", "run", "web/interactive_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
