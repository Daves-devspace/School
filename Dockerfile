# Use a slim version of Python 3.12 as the base image
FROM python:3.12-slim

# Install necessary tools, system dependencies, and Netcat for database readiness checks
RUN apt-get update && apt-get install -y \
    curl \
    file \
    gcc \
    default-mysql-client \
    default-libmysqlclient-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libgtk-3-0 \
    libjpeg-dev \
    libpq-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libglib2.0-dev \
    libffi-dev \
    netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables to ensure proper behavior
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory for the application
WORKDIR /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip

# Copy the requirements file first to leverage Docker caching
COPY requirements.txt /app/

# Install Python dependencies using the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files to the container
COPY . /app/

# Copy entrypoint.sh to the container
COPY entrypoint.sh /entrypoint.sh

# Make entrypoint.sh executable
RUN chmod +x /entrypoint.sh

# Set the entrypoint to use the script
ENTRYPOINT ["/entrypoint.sh"]

# Expose the port your app will be running on
EXPOSE 8000

# Command to run the application using Gunicorn for production
CMD ["gunicorn", "School.wsgi:application", "--bind", "0.0.0.0:8000"]
