# Gunakan base image yang sudah ditentukan
FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel

# Atur working directory
WORKDIR /app

# Salin semua file dan folder yang diperlukan
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "huggingface_hub[cli]" gradio

# Buat direktori untuk model dan entrypoint script
RUN mkdir -p /app/Wan2.1-T2V-1.3B /app/Phantom-Wan-Models
COPY download_models.sh /app/download_models.sh
RUN chmod +x /app/download_models.sh

# Expose port Gradio
EXPOSE 7860

# Entrypoint akan mengunduh model dan menjalankan aplikasi Gradio
ENTRYPOINT ["/app/download_models.sh"]
