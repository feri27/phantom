# Use the specified base image
# FROM iavas/runpod-pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04
FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel

# Set a working directory
WORKDIR /app

# Copy the application files
COPY generate.py requirements.txt ./
# The Gradio UI code will be saved in a new file, e.g., app.py
COPY app.py ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "huggingface_hub[cli]" gradio

# Create a directory for models and an entrypoint script
RUN mkdir -p /app/Wan2.1-T2V-1.3B /app/Phantom-Wan-Models
COPY download_models.sh /app/download_models.sh
RUN chmod +x /app/download_models.sh

# Expose the Gradio port
EXPOSE 7860

# The entrypoint will download the models and then run the Gradio app
ENTRYPOINT ["/app/download_models.sh"]
