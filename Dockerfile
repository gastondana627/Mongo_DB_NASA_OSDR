# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container at /app
COPY . .

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define the command to run your app using streamlit
# The --server.address=0.0.0.0 is crucial for it to be accessible in the cloud
CMD ["streamlit", "run", "streamlit_main_app.py", "--server.port=8501", "--server.address=0.0.0.0"]


