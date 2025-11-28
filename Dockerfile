# Use the official Python image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /code

# Copy requirements and packages first to leverage Docker cache
COPY ./requirements.txt /code/requirements.txt
COPY ./packages.txt /code/packages.txt

# Install system dependencies (Tesseract) from packages.txt
RUN apt-get update && xargs -a packages.txt apt-get install -y && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the app code
COPY . .

# Expose the port Hugging Face expects
EXPOSE 7860

# Run the application
# NOTE: Ensure your main file is named 'app.py'. If it is 'main.py', change it below.
CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "7860"]
