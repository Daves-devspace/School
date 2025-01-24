FROM python:3.12-slim

# Install necessary tools and dependencies
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

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into the container
COPY . /app/

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Expose the dynamic port for Render
EXPOSE 8000

# Command to run Gunicorn, use the dynamic port set by Render
CMD ["gunicorn", "School.wsgi:application", "--bind", "0.0.0.0:8000"]
