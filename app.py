"""
Gradio UI for Phantom Video Generation
"""
import gradio as gr
import requests
import os
import subprocess
import uuid
import tempfile
import shutil
from pathlib import Path
import cv2
import numpy as np

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
EXAMPLES_DIR = Path("examples")

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_video(
    prompt,
    reference_image,
    resolution,
    base_seed,
    model_choice,
    num_frames,
    fps,
    progress=gr.Progress()
):
    """Generate video using Phantom model"""
    
    if not prompt.strip():
        return None, "Please enter a prompt"
    
    progress(0.1, desc="Preparing generation...")
    
    try:
        # Generate unique ID
        request_id = str(uuid.uuid4())
        
        # Prepare paths
        output_path = OUTPUT_DIR / f"{request_id}_output.mp4"
        
        # Handle reference image
        ref_image_path = None
        if reference_image is not None:
            ref_image_path = UPLOAD_DIR / f"{request_id}_ref.png"
            # Save uploaded image
            with open(ref_image_path, "wb") as f:
                f.write(reference_image)
        
        progress(0.2, desc="Setting up model...")
        
        # Map model choice to path
        model_paths = {
            "Phantom-Wan-1.3B": "models/Phantom-Wan-1.3B",
            "Wan2.1-T2V-1.3B": "models/Wan2.1-T2V-1.3B"
        }
        model_path = model_paths.get(model_choice, "models/Phantom-Wan-1.3B")
        
        # Build command
        cmd = [
            "python", "generate.py",
            "--prompt", prompt,
            "--model_path", model_path,
            "--resolution", resolution,
            "--base_seed", str(base_seed),
            "--num_frames", str(num_frames),
            "--fps", str(fps),
            "--output", str(output_path)
        ]
        
        if ref_image_path and ref_image_path.exists():
            cmd.extend(["--reference_image", str(ref_image_path)])
        
        progress(0.3, desc="Running inference...")
        
        # Run generation
        print(f"Running: {' '.join(cmd)}")
        
        # Use Popen for better progress tracking
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            universal_newlines=True
        )
        
        # Monitor progress
        for i in range(30):  # Simulate progress
            if process.poll() is not None:
                break
            progress(0.3 + (i * 0.02), desc=f"Generating video... ({i+1}/30)")
            import time
            time.sleep(2)
        
        stdout, stderr = process.communicate(timeout=300)
        
        if process.returncode != 0:
            error_msg = f"Generation failed:\n{stderr}\n{stdout}"
            print(error_msg)
            return None, error_msg
        
        progress(0.9, desc="Finalizing...")
        
        # Check if output exists
        if not output_path.exists():
            return None, "Output video was not generated. Check model paths and dependencies."
        
        progress(1.0, desc="Complete!")
        
        # Return the video path and success message
        return str(output_path), f"✅ Video generated successfully!\nOutput: {output_path.name}"
        
    except subprocess.TimeoutExpired:
        return None, "⏰ Generation timeout. Try reducing frames or simplifying prompt."
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(error_msg)
        return None, error_msg

def get_example_images():
    """Get list of example reference images"""
    example_images = []
    if EXAMPLES_DIR.exists():
        for img_path in EXAMPLES_DIR.glob("ref*.png"):
            example_images.append(str(img_path))
    return example_images[:5]  # Limit to 5 examples

# Example prompts
EXAMPLE_PROMPTS = [
    "A beautiful sunset over the ocean with gentle waves",
    "A cat walking through a garden with flowers blooming",
    "Rain drops falling on a window with city lights in background",
    "Smoke rising from a cup of coffee on a wooden table",
    "Leaves falling from a tree in autumn wind"
]

# Create Gradio interface
def create_interface():
    with gr.Blocks(
        title="Phantom Video Generation",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .generate-btn {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
            color: white !important;
            font-weight: bold !important;
        }
        """
    ) as iface:
        
        gr.Markdown("""
        # 🎬 Phantom Video Generation
        
        Generate high-quality videos from text prompts using the Phantom-Wan-1.3B model.
        
        **Features:**
        - Subject-consistent video generation
        - Reference image support
        - Customizable resolution and frame count
        - Fast inference with optimized models
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Input Settings")
                
                prompt = gr.Textbox(
                    label="Text Prompt",
                    placeholder="Describe the video you want to generate...",
                    lines=3,
                    value="A beautiful sunset over the ocean with gentle waves"
                )
                
                with gr.Row():
                    prompt_examples = gr.Examples(
                        examples=EXAMPLE_PROMPTS,
                        inputs=prompt,
                        label="Example Prompts"
                    )
                
                reference_image = gr.File(
                    label="Reference Image (Optional)",
                    file_types=["image"],
                    type="binary"
                )
                
                with gr.Row():
                    resolution = gr.Dropdown(
                        choices=["512x320", "768x512", "1024x640"],
                        value="512x320",
                        label="Resolution"
                    )
                    
                    model_choice = gr.Dropdown(
                        choices=["Phantom-Wan-1.3B", "Wan2.1-T2V-1.3B"],
                        value="Phantom-Wan-1.3B",
                        label="Model"
                    )
                
                with gr.Row():
                    num_frames = gr.Slider(
                        minimum=16,
                        maximum=50,
                        value=25,
                        step=1,
                        label="Number of Frames"
                    )
                    
                    fps = gr.Slider(
                        minimum=4,
                        maximum=24,
                        value=8,
                        step=1,
                        label="FPS"
                    )
                
                base_seed = gr.Number(
                    value=42,
                    label="Seed (for reproducibility)",
                    precision=0
                )
                
                generate_btn = gr.Button(
                    "🎬 Generate Video",
                    variant="primary",
                    elem_classes=["generate-btn"]
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 🎥 Output")
                
                output_video = gr.Video(
                    label="Generated Video",
                    height=400
                )
                
                output_message = gr.Textbox(
                    label="Status",
                    lines=3,
                    max_lines=5
                )
                
                gr.Markdown("""
                ### 💡 Tips:
                - Use descriptive prompts for better results
                - Reference images help maintain subject consistency
                - Lower frame counts generate faster
                - Higher FPS creates smoother motion
                - Experiment with different seeds for variation
                """)
        
        # Connect the generate button
        generate_btn.click(
            fn=generate_video,
            inputs=[
                prompt,
                reference_image,
                resolution,
                base_seed,
                model_choice,
                num_frames,
                fps
            ],
            outputs=[output_video, output_message],
            show_progress=True
        )
        
        gr.Markdown("""
        ---
        
        **Phantom Video Generation Framework** | Powered by Phantom-Wan-1.3B
        
        For more information, visit: [GitHub Repository](https://github.com/feri27/phantom)
        """)
    
    return iface

if __name__ == "__main__":
    # Create and launch interface
    demo = create_interface()
    
    # Launch with configuration
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        show_tips=True,
        enable_queue=True,
        max_threads=1
    )
