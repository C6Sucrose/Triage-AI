# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (needed for compiling some Python packages)
RUN apt-get update && apt-get install -y build-essential

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies into a localized directory
RUN pip install --user --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /root/.local /root/.local

# Make sure the installed binaries are on the PATH
ENV PATH=/root/.local/bin:$PATH

# Copy the actual application code
COPY . .

# Expose port 8080 (Standard for Google Cloud Run)
EXPOSE 8080

# Start the FastAPI server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]