FROM python:3.11-slim-bookworm 

# Install required system packages, including PostgreSQL client libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        g++ \
        libpq-dev \
        libpq5 \
        postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /usr/src/app/

# Copy requirements and install dependencies
COPY requirements.txt . 
RUN pip install -r requirements.txt

# Copy the application files
COPY locustfile.py .

# Define the entrypoint for Locust
ENTRYPOINT ["locust", "--skip-log-setup"]