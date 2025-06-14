FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r snmpsim && useradd -r -g snmpsim -u 1001 snmpsim

# Install snmpsim
RUN pip install --no-cache-dir snmpsim-lextudio==1.1.1

# Create data directory and set permissions
RUN mkdir -p /usr/local/snmpsim/data && \
    chown -R snmpsim:snmpsim /usr/local/snmpsim

# Copy our test data if available
COPY data/ /usr/local/snmpsim/data/

# Set ownership of copied data
RUN chown -R snmpsim:snmpsim /usr/local/snmpsim/data

# Switch to non-root user
USER snmpsim

# Expose SNMP port
EXPOSE 161/udp

# Default command - no privilege dropping needed since we're already non-root
CMD ["snmpsim-command-responder", \
     "--data-dir=/usr/local/snmpsim/data", \
     "--agent-udpv4-endpoint=0.0.0.0:161"]
