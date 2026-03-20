FROM python:3.13-slim

# Install Icarus Verilog
RUN apt-get update && \
    apt-get install -y --no-install-recommends iverilog make && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir cocotb==2.0.1

# Copy project files
WORKDIR /app
COPY src/ src/
COPY prompts/ prompts/

# Run the watcher with Anthropic API backend
CMD ["python3", "-m", "src.watcher", "--backend", "anthropic_api"]
