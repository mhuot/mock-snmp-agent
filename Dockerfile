FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install snmpsim
RUN pip install --no-cache-dir snmpsim-lextudio==1.1.1

# Create data directory
RUN mkdir -p /usr/local/snmpsim/data

# Copy our test data if available
COPY data/ /usr/local/snmpsim/data/

# Expose SNMP port
EXPOSE 161/udp

# Default command
CMD ["snmpsim-command-responder", \
     "--data-dir=/usr/local/snmpsim/data", \
     "--agent-udpv4-endpoint=0.0.0.0:161"]