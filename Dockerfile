# Base image
FROM python:3.11

# Prevent interactive prompts and ensure pip-installed scripts are in PATH
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:$PATH"

# Install only verified, existing Debian Bookworm packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb x11vnc \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb1 \
    libasound2 \
    libxrender1 \
    libatk1.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    git curl wget unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Camoufox CLI
RUN pip install --no-cache-dir Camoufox

# Copy application code
COPY . /app/

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Entrypoint runs start.sh
ENTRYPOINT ["/start.sh"]
CMD []
