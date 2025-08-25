#!/bin/bash

echo "Starting model download script..."

# Check if HUGGING_FACE_HUB_TOKEN is set
if [ -z "$HUGGING_FACE_HUB_TOKEN" ]; then
    echo "HUGGING_FACE_HUB_TOKEN environment variable not set. Please provide your Hugging Face access token."
    exit 1
fi

# Log in using the environment variable
echo "Attempting to log in to Hugging Face CLI with provided token..."
huggingface-cli login --token $HUGGING_FACE_HUB_TOKEN

# Download Wan2.1-T2V-1.3B model
echo "Downloading Wan2.1-T2V-1.3B..."
huggingface-cli download Wan-AI/Wan2.1-T2V-1.3B --local-dir ./Wan2.1-T2V-1.3B --resume-download

# Download Phantom-Wan models
echo "Downloading Phantom-Wan models..."
huggingface-cli download bytedance-research/Phantom --local-dir ./Phantom-Wan-Models --resume-download

echo "Model download complete. Starting Gradio app..."

# Run the Gradio app
python app.py
