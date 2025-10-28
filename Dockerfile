# Multi-stage Dockerfile for Renify Bot with Lavalink
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_VERSION=17
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    netcat-openbsd \
    openjdk-17-jdk \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Download Lavalink
RUN wget -q https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar -O Lavalink.jar

# Copy application files
COPY renify_core.py .
COPY application.yml .

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Lavalink in background\n\
echo "Starting Lavalink..."\n\
java -jar Lavalink.jar --spring.config.location=application.yml &\n\
LAVALINK_PID=$!\n\
echo "Lavalink started with PID: $LAVALINK_PID"\n\
\n\
# Wait for Lavalink to be ready with HTTP check\n\
echo "Waiting for Lavalink to start..."\n\
for i in {1..60}; do\n\
    if curl -fsS http://lavalink:2333/version > /dev/null 2>&1; then\n\
        echo "Lavalink is ready on port 2333!"\n\
        # Give it a moment to fully initialize\n\
        sleep 3\n\
        break\n\
    fi\n\
    echo "Attempt $i/60: Lavalink not ready yet..."\n\
    sleep 2\n\
done\n\
\n\
# Check if Lavalink is actually running\n\
if ! curl -fsS http://lavalink:2333/version > /dev/null 2>&1; then\n\
    echo "ERROR: Lavalink failed to start on port 2333!"\n\
    echo "Lavalink process status:"\n\
    ps aux | grep java\n\
    exit 1\n\
fi\n\
\n\
# Start the Python bot\n\
echo "Starting Renify bot..."\n\
exec python3 renify_core.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 2333

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://lavalink:2333/version || exit 1

# Start both services
CMD ["/app/start.sh"]

