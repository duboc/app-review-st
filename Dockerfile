FROM python:3.12

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (replace with your values)
ENV STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true
ENV GCP_PROJECT=conventodapenha

EXPOSE 8080

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8080"]