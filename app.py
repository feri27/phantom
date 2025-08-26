import gradio as gr
import subprocess
import os
import shutil
import random
import re
import time
from PIL import Image
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

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
    """Update default values based on selected task"""
    config = TASKS.get(task, {})
    return (
        config.get("size", "1280*720"),
        config.get("frame_num", 81),
        config.get("sample_steps", 50),
        config.get("sample_solver", "unipc"),
        config.get("sample_shift", 5.0)
    )

def validate_frame_num(frame_num):
    """Ensure frame_num follows 4n+1 rule"""
    if (frame_num - 1) % 4 != 0:
        adjusted = ((frame_num - 1) // 4) * 4 + 1
        return adjusted
    return frame_num

def get_generated_files():
    """Scan generated_outputs folder and return list of file paths"""
    output_dir = "generated_outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        return []
    
    file_paths = []
    for f in os.listdir(output_dir):
        full_path = os.path.join(output_dir, f)
        if os.path.isfile(full_path):
            file_paths.append(full_path)
    
    # Sort by modification time, newest first
    file_paths.sort(key=os.path.getmtime, reverse=True)
    return file_paths

def get_generated_files_with_preview():
    """Get generated files and return preview for the latest file"""
    files = get_generated_files()
    if not files:
        return files, gr.update(visible=False), gr.update(visible=False)
    
    # Get the latest file for preview
    latest_file = files[0]
    if latest_file.endswith('.mp4'):
        return files, gr.update(value=latest_file, visible=True), gr.update(visible=False)
    elif latest_file.endswith(('.png', '.jpg', '.jpeg')):
        return files, gr.update(visible=False), gr.update(value=latest_file, visible=True)
    else:
        return files, gr.update(visible=False), gr.update(visible=False)

def check_model_requirements(task):
    """Check if required models exist for the given task"""
    missing_models = []
    
    # Check base model
    if not os.path.exists("./Wan2.1-T2V-1.3B"):
        missing_models.append("Wan2.1-T2V-1.3B")
    
    # Check phantom models for s2v tasks
    if "s2v" in task:
        if "1.3B" in task and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-1.3B.pth"):
            missing_models.append("Phantom-Wan-1.3B.pth")
        elif "14B" in task and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-14B.pth"):
            missing_models.append("Phantom-Wan-14B.pth")
    
    return missing_models

def prepare_reference_images(ref_images, task):
    """Prepare reference images for s2v tasks"""
    if not ref_images or "s2v" not in task:
        return []
    
    # Limit to 4 images as per the model requirements
    ref_images = ref_images[:4]
    
    ref_image_dir = "temp_ref_images"
    shutil.rmtree(ref_image_dir, ignore_errors=True)
    os.makedirs(ref_image_dir, exist_ok=True)
    
    ref_image_paths = []
    for i, img_path in enumerate(ref_images):
        try:
            with Image.open(img_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                temp_path = os.path.join(ref_image_dir, f"ref_img_{i}.png")
                img.save(temp_path)
                ref_image_paths.append(temp_path)
        except Exception as e:
            logging.error(f"Error processing reference image {i}: {str(e)}")
    
    return ref_image_paths

def generate_video_or_image(
    task,
    prompt,
    ref_images,
    size,
    frame_num,
    sample_steps,
    sample_solver,
    sample_shift,
    base_seed,
    guide_scale_img=5.0,
    guide_scale_text=7.5
):
    """Main generation function"""
    
    # Validate inputs
    if not prompt or not prompt.strip():
        yield "❌ Error: Prompt cannot be empty.", None, gr.update(visible=False), gr.update(visible=False)
        return
    
    # Check model requirements
    missing_models = check_model_requirements(task)
    if missing_models:
        error_msg = f"❌ Error: Missing required models: {', '.join(missing_models)}\n"
        error_msg += "Please run the model download script first."
        yield error_msg, None, gr.update(visible=False), gr.update(visible=False)
        return
    
    # Validate and adjust frame_num
    original_frame_num = frame_num
    frame_num = validate_frame_num(frame_num)
    if frame_num != original_frame_num:
        yield f"⚠️ Warning: Frame number adjusted from {original_frame_num} to {frame_num} (must follow 4n+1 rule)\n", None, gr.update(visible=False), gr.update(visible=False)
    
    # Handle random seed
    if base_seed < 0:
        base_seed = random.randint(0, 2147483647)
    
    # Prepare output
    sanitized_prompt = re.sub(r'[^a-zA-Z0-9_ -]', '', prompt).replace(" ", "_")[:50]
    output_dir = "generated_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = int(time.time())
    save_file = os.path.join(output_dir, f"{task}_{sanitized_prompt}_{timestamp}")
    
    # Prepare reference images for s2v tasks
    ref_image_paths = prepare_reference_images(ref_images, task)
    
    # Build command
    command = [
        "python", "generate.py",
        "--task", task,
        "--prompt", prompt,
        "--size", size,
        "--frame_num", str(frame_num),
        "--sample_steps", str(sample_steps),
        "--sample_solver", sample_solver,
        "--sample_shift", str(sample_shift),
        "--base_seed", str(base_seed),
        "--ckpt_dir", "./Wan2.1-T2V-1.3B",
        "--save_file", save_file
    ]
    
    # Add task-specific parameters
    if "s2v" in task:
        phantom_ckpt_path = "./Phantom-Wan-Models/Phantom-Wan-1.3B.pth" if "1.3B" in task else "./Phantom-Wan-Models/Phantom-Wan-14B.pth"
        command.extend(["--phantom_ckpt", phantom_ckpt_path])
        
        if ref_image_paths:
            command.extend(["--ref_image", ",".join(ref_image_paths)])
        
        # Add guidance scales for s2v
        command.extend([
            "--sample_guide_scale_img", str(guide_scale_img),
            "--sample_guide_scale_text", str(guide_scale_text)
        ])
    else:
        # For other tasks, use single guidance scale
        guide_scale = guide_scale_img  # Use img scale as default
        command.extend(["--sample_guide_scale", str(guide_scale)])
    
    # Set environment variable
    env = os.environ.copy()
    env['MKL_SERVICE_FORCE_INTEL'] = '1'
    
    # Initial status
    yield f"🚀 Starting generation with task: {task}\n" + \
          f"📝 Prompt: {prompt}\n" + \
          f"🎯 Seed: {base_seed}\n" + \
          f"📐 Size: {size}\n" + \
          f"🎬 Frames: {frame_num}\n" + \
          f"⚙️ Steps: {sample_steps}\n" + \
          "=" * 50 + "\n", None, gr.update(visible=False), gr.update(visible=False)
    
    # Run generation
    try:
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            env=env,
            bufsize=1,
            universal_newlines=True
        )
        
        output_lines = []
        
        # Read output in real-time
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                output_lines.append(line.rstrip())
                # Show last 20 lines to prevent overflow
                display_lines = output_lines[-20:] if len(output_lines) > 20 else output_lines
                current_output = f"🚀 Starting generation with task: {task}\n" + \
                               f"📝 Prompt: {prompt}\n" + \
                               f"🎯 Seed: {base_seed}\n" + \
                               f"📐 Size: {size}\n" + \
                               f"🎬 Frames: {frame_num}\n" + \
                               f"⚙️ Steps: {sample_steps}\n" + \
                               "=" * 50 + "\n" + \
                               "\n".join(display_lines)
                yield current_output, None, gr.update(visible=False), gr.update(visible=False)
        
        # Check for errors
        stderr_output = process.stderr.read()
        
        if process.returncode != 0:
            error_msg = f"❌ Generation failed with return code {process.returncode}\n"
            if stderr_output:
                error_msg += f"Error details:\n{stderr_output}"
            yield error_msg, None, gr.update(visible=False), gr.update(visible=False)
            return
        
        # Check if output file was created
        expected_extensions = ['.mp4', '.png']
        output_file = None
        
        for ext in expected_extensions:
            potential_file = save_file + ext
            if os.path.exists(potential_file):
                output_file = potential_file
                break
        
        if output_file and os.path.exists(output_file):
            final_output = "\n".join(output_lines) + f"\n\n✅ Generation completed successfully!\n🎉 Output saved to: {output_file}"
            
            # Return the generated file for preview and file list
            generated_files = get_generated_files()
            
            # Determine if it's video or image and return appropriate preview
            if output_file.endswith('.mp4'):
                yield final_output, generated_files, gr.update(value=output_file, visible=True), gr.update(visible=False)
            else:  # image
                yield final_output, generated_files, gr.update(visible=False), gr.update(value=output_file, visible=True)
        else:
            yield "⚠️ Generation completed but output file not found.", get_generated_files(), gr.update(visible=False), gr.update(visible=False)
    
    except Exception as e:
        yield f"❌ Unexpected error during generation: {str(e)}", None, gr.update(visible=False), gr.update(visible=False)
    
    finally:
        # Cleanup temporary files
        if os.path.exists("temp_ref_images"):
            shutil.rmtree("temp_ref_images", ignore_errors=True)

def update_guidance_visibility(task):
    """Update visibility of guidance scale controls based on task"""
    if "s2v" in task:
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

# Create Gradio interface
with gr.Blocks(title="Phantom-Wan Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 👻 Phantom-Wan: Subject-Consistent Video Generation
        Generate high-quality videos and images with subject consistency using the Phantom-Wan model.
        
        **Supported Tasks:**
        - **s2v** (Subject-to-Video): Generate videos with subject consistency using reference images
        - **t2v** (Text-to-Video): Generate videos from text prompts
        - **t2i** (Text-to-Image): Generate images from text prompts  
        - **i2v** (Image-to-Video): Generate videos from input images
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                task_selector = gr.Dropdown(
                    label="🎯 Task",
                    choices=list(TASKS.keys()),
                    value="s2v-1.3B",
                    interactive=True,
                    info="Select the generation task"
                )
                
                prompt_input = gr.Textbox(
                    label="📝 Prompt",
                    placeholder="Enter your detailed prompt here...",
                    lines=3,
                    info="Describe what you want to generate"
                )
                
                ref_image_gallery = gr.File(
                    label="🖼️ Reference Images (for s2v tasks only)",
                    file_count="multiple",
                    file_types=["image"],
                    interactive=True,
                    info="Upload up to 4 reference images for subject consistency"
                )
        
        with gr.Column(scale=1):
            with gr.Accordion("⚙️ Advanced Settings", open=False):
                with gr.Row():
                    size_dropdown = gr.Dropdown(
                        label="📐 Size",
                        choices=SUPPORTED_SIZES,
                        value="832*480",
                        interactive=True,
                        info="Output resolution"
                    )
                    frame_num_slider = gr.Slider(
                        label="🎬 Frame Number",
                        minimum=1,
                        maximum=201,
                        step=4,
                        value=81,
                        interactive=True,
                        info="Number of frames (will be adjusted to 4n+1)"
                    )
                
                with gr.Row():
                    sample_steps_slider = gr.Slider(
                        label="🔧 Sampling Steps",
                        minimum=10,
                        maximum=100,
                        step=1,
                        value=40,
                        interactive=True,
                        info="More steps = higher quality but slower"
                    )
                    sample_solver_dropdown = gr.Dropdown(
                        label="🧮 Sample Solver",
                        choices=['unipc', 'dpm++'],
                        value='unipc',
                        interactive=True,
                        info="Sampling algorithm"
                    )
                
                with gr.Row():
                    sample_shift_slider = gr.Slider(
                        label="⚡ Sample Shift",
                        minimum=0.1,
                        maximum=10.0,
                        step=0.1,
                        value=5.0,
                        interactive=True,
                        info="Flow matching shift factor"
                    )
                    base_seed_number = gr.Number(
                        label="🎲 Seed",
                        value=-1,
                        step=1,
                        interactive=True,
                        info="Use -1 for random seed"
                    )
                
                # Guidance scale controls
                with gr.Group():
                    guide_scale_img_slider = gr.Slider(
                        label="🎨 Image Guidance Scale",
                        minimum=1.0,
                        maximum=20.0,
                        step=0.1,
                        value=5.0,
                        interactive=True,
                        info="Guidance scale for reference images (s2v tasks)",
                        visible=True
                    )
                    guide_scale_text_slider = gr.Slider(
                        label="📝 Text Guidance Scale", 
                        minimum=1.0,
                        maximum=20.0,
                        step=0.1,
                        value=7.5,
                        interactive=True,
                        info="Guidance scale for text prompts (s2v tasks)",
                        visible=True
                    )
                    guide_scale_single_slider = gr.Slider(
                        label="🎛️ Guidance Scale",
                        minimum=1.0,
                        maximum=20.0,
                        step=0.1,
                        value=5.0,
                        interactive=True,
                        info="Classifier-free guidance scale",
                        visible=False
                    )

    generate_btn = gr.Button("🚀 Generate!", variant="primary", size="lg")
    
    with gr.Row():
        with gr.Column():
            output_log = gr.Textbox(
                label="📋 Process Log", 
                lines=15, 
                max_lines=15, 
                interactive=False,
                show_copy_button=True
            )
        with gr.Column():
            # Preview area for generated content
            with gr.Group():
                gr.Markdown("### 🎬 Generated Content")
                output_video = gr.Video(
                    label="Generated Video",
                    visible=False,
                    interactive=False
                )
                output_image = gr.Image(
                    label="Generated Image", 
                    visible=False,
                    interactive=False,
                    type="filepath"
                )
            
            # File download area
            output_file_list = gr.File(
                label="📁 All Generated Files", 
                file_count="multiple", 
                interactive=False,
                info="Click to download generated files"
            )

    # Event handlers
    task_selector.change(
        fn=update_defaults,
        inputs=[task_selector],
        outputs=[size_dropdown, frame_num_slider, sample_steps_slider, sample_solver_dropdown, sample_shift_slider]
    )
    
    task_selector.change(
        fn=update_guidance_visibility,
        inputs=[task_selector],
        outputs=[guide_scale_img_slider, guide_scale_text_slider, guide_scale_single_slider]
    )

    generate_btn.click(
        fn=generate_video_or_image,
        inputs=[
            task_selector,
            prompt_input,
            ref_image_gallery,
            size_dropdown,
            frame_num_slider,
            sample_steps_slider,
            sample_solver_dropdown,
            sample_shift_slider,
            base_seed_number,
            guide_scale_img_slider,
            guide_scale_text_slider
        ],
        outputs=[output_log, output_file_list, output_video, output_image]
    )

    # Load generated files on startup with preview
    demo.load(
        fn=get_generated_files_with_preview, 
        outputs=[output_file_list, output_video, output_image]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        show_error=True,
        show_tips=True
    )