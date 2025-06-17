FROM python:3.11-slim

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . .

# Make sure entrypoint is executable
RUN chmod +x entrypoint.sh

# Run entrypoint (Streamlit runs from here)
ENTRYPOINT ["./entrypoint.sh"]

# Required for Cloud Run
EXPOSE 8080


