# Multi-stage build for Portfolio Spoke MCP Server
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY ./services/portfolio-spoke/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r portfolio && useradd -r -g portfolio portfolio

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/portfolio/.local

# Copy shared libraries
COPY ./shared /app/shared

# Copy application code
COPY ./services/portfolio-spoke/app/ ./app/
COPY --from=builder /app /app

# Set environment variables
ENV PATH=/home/portfolio/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Change ownership to non-root user
RUN chown -R portfolio:portfolio /app
USER portfolio

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health')" || exit 1

# Expose port
EXPOSE 8003

# Start command
CMD ["python", "-m", "mcp_server"]
