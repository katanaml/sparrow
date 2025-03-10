# Base Image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpoppler-cpp-dev \
    libgl1 \
    cmake \
    build-essential \
    && pip install --no-cache-dir --upgrade pip

# Copy the requirements file to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Expose the port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
