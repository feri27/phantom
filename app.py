import gradio as gr
import subprocess
import os
import shutil
import random
import re
from PIL import Image

# Define the tasks and their default settings based on generate.py and README.md
TASKS = {
    "s2v-1.3B": {
        "size": "832*480",
        "frame_num": 81,
        "sample_steps": 40,
        "sample_solver": "unipc",
        "sample_shift": 5.0,
        "guide_scale_img": 5.0,
        "guide_scale_text": 7.5
    },
    "s2v-14B": {
        "size": "832*480",
        "frame_num": 121,
        "sample_steps": 40,
        "sample_solver": "unipc",
        "sample_shift": 5.0,
        "guide_scale_img": 5.0,
        "guide_scale_text": 7.5
    },
    "t2v-1.3B": {
        "size": "1280*720",
        "frame_num": 81,
        "sample_steps": 50,
        "sample_solver": "unipc",
        "sample_shift": 5.0,
        "guide_scale": 5.0
    },
    "t2v-14B": {
        "size": "1280*720",
        "frame_num": 81,
        "sample_steps": 50,
        "sample_solver": "unipc",
        "sample_shift": 5.0,
        "guide_scale": 5.0
    },
    "t2i-14B": {
        "size": "1280*720",
        "frame_num": 1,
        "sample_steps": 50,
        "sample_solver": "unipc",
        "sample_shift": 5.0,
        "guide_scale": 5.0
    },
    "i2v-14B": {
        "size": "1280*720",
        "frame_num": 81,
        "sample_steps": 40,
        "sample_solver": "unipc",
        "sample_shift": 3.0,
        "guide_scale": 5.0
    }
}

SUPPORTED_SIZES = ["1280*720", "720*1280", "832*480", "480*832", "1024*576", "576*1024", "720*480", "480*720", "640*480", "480*640", "1024*1024"]

def update_defaults(task):
    config = TASKS.get(task, {})
    return (
        config.get("size", "1280*720"),
        config.get("frame_num", 81),
        config.get("sample_steps", 50),
        config.get("sample_solver", "unipc"),
        config.get("sample_shift", 5.0)
    )

def get_generated_files():
    """Memindai folder generated_outputs dan mengembalikan list path file."""
    output_dir = "generated_outputs"
    if not os.path.exists(output_dir):
        return []
    
    file_paths = [os.path.join(output_dir, f) for f in os.listdir(output_dir) 
                  if os.path.isfile(os.path.join(output_dir, f)) and 
                  (f.endswith('.mp4') or f.endswith('.png'))]
    file_paths.sort(key=os.path.getmtime, reverse=True)
    return file_paths

def check_file_size(file_path):
    """Cek ukuran file untuk memastikan tidak kosong."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def validate_video_file(file_path):
    """Validasi apakah file video dapat diputar."""
    try:
        import cv2
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return False
        
        # Coba baca frame pertama
        ret, frame = cap.read()
        cap.release()
        return ret and frame is not None
    except:
        return False