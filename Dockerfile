# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/feri27/phantom.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for Gradio and API
RUN pip install --no-cache-dir \
    gradio \
    fastapi \
    uvicorn \
    python-multipart \
    Pillow \
    opencv-python \
    huggingface_hub

# Create directories for models
RUN mkdir -p models/Wan2.1-T2V-1.3B models/Phantom-Wan-1.3B

# Download models from Hugging Face
RUN python -c "
import os
from huggingface_hub import snapshot_download

# Download Wan2.1-T2V-1.3B model
print('Downloading Wan2.1-T2V-1.3B model...')
snapshot_download(
    repo_id='Phantom-video/Wan2.1-T2V-1.3B',
    local_dir='models/Wan2.1-T2V-1.3B',
    local_dir_use_symlinks=False
)

# Download Phantom-Wan-1.3B model
print('Downloading Phantom-Wan-1.3B model...')
snapshot_download(
    repo_id='Phantom-video/Phantom-Wan-1.3B',
    local_dir='models/Phantom-Wan-1.3B',
    local_dir_use_symlinks=False
)

print('Models downloaded successfully!')
"

# Copy application files
COPY app.py .
COPY api_server.py .

# Create output directory
RUN mkdir -p outputs

# Expose port for Gradio
EXPOSE 7860

# Set environment variables
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0

# Default command to run Gradio app
CMD ["python", "app.py"]
