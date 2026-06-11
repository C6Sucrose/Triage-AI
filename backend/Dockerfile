# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies (needed for compiling some Python packages)
RUN apt-get update && apt-get install -y build-essential

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies into a neutral prefix directory (not tied to any user's home)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

# Create non-root user for security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 appuser --ingroup appgroup --home /home/appuser

# Copy installed dependencies from builder into the global Python path
# (/usr/local is always on sys.path regardless of which user runs Python)
COPY --from=builder /install /usr/local

# Copy the application code and set ownership
COPY --chown=appuser:appgroup . . .

# Switch to non-root user
USER appuser

# Expose port 8080 (Standard for Google Cloud Run)
EXPOSE 8080

# Start the FastAPI server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]