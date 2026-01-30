FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY app.py .
COPY src/ ./src/
COPY api/ ./api/

EXPOSE 8501

# Run Streamlit (FastAPI can be added as second service later)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]