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
):
    if not prompt:
        yield "Prompt cannot be empty.", None, None
        return
    
    # Check for model existence
    if not os.path.exists("./Wan2.1-T2V-1.3B"):
        yield "Wan2.1-T2V-1.3B model not found. Please run the model download script.", None, None
        return
    
    if task == "s2v-1.3B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-1.3B.pth"):
        yield "Phantom-Wan-1.3B model not found. Please run the model download script.", None, None
        return
    elif task == "s2v-14B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-14B.pth"):
        yield "Phantom-Wan-14B model not found. Please run the model download script.", None, None
        return

    # Sanitize prompt for filename
    sanitized_prompt = re.sub(r'[^a-zA-Z0-9_ -]', '', prompt).replace(" ", "_").replace("/", "_")[:50]
    output_dir = "generated_outputs"
    os.makedirs(output_dir, exist_ok=True)
    save_file = os.path.join(output_dir, f"{sanitized_prompt}_{random.randint(1000, 9999)}")
    
    # Save reference images to a temporary directory
    ref_image_paths = []
    if ref_images and "s2v" in task:
        ref_image_dir = "temp_ref_images"
        shutil.rmtree(ref_image_dir, ignore_errors=True)
        os.makedirs(ref_image_dir)
        for i, img_path in enumerate(ref_images):
            with Image.open(img_path) as img:
                temp_path = os.path.join(ref_image_dir, f"ref_img_{i}.png")
                img.save(temp_path)
                ref_image_paths.append(temp_path)
    
    # Construct the command
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

    if "s2v" in task:
        phantom_ckpt_path = "./Phantom-Wan-Models/Phantom-Wan-1.3B.pth" if "1.3B" in task else "./Phantom-Wan-Models/Phantom-Wan-14B.pth"
        command.extend(["--phantom_ckpt", phantom_ckpt_path])
        if ref_image_paths:
            command.extend(["--ref_image", ",".join(ref_image_paths)])

    os.environ['MKL_SERVICE_FORCE_INTEL'] = '1'
    
    # Run the command
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Stream output to Gradio
    output_log_list = []
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            output_log_list.append(line)
            # Yield three values to update output_log, output_image, and output_video
            yield "\n".join(output_log_list), None, None
    
    stderr = process.stderr.read()
    if process.returncode != 0:
        yield f"Error during generation: {stderr}", None, None
        return

    # Determine output path and type
    final_log = "\n".join(output_log_list)

    if "t2i" in task:
        result_path = f"{save_file}.png"
        yield final_log, result_path, None
    else:
        result_path = f"{save_file}.mp4"
        yield final_log, None, result_path

with gr.Blocks(title="Phantom-Wan Generator") as demo:
    gr.Markdown("# 👻 Phantom-Wan: Subject-Consistent Video Generation")
    gr.Markdown("Generate videos and images with subject consistency using the Phantom-Wan model.")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                task_selector = gr.Dropdown(
                    label="Task",
                    choices=list(TASKS.keys()),
                    value="s2v-1.3B",
                    interactive=True
                )
                prompt_input = gr.Textbox(
                    label="Prompt",
                    placeholder="Enter your prompt here."
                )
                
                ref_image_gallery = gr.File(
                    label="Reference Images (for s2v tasks, up to 4)",
                    file_count="multiple",
                    file_types=["image"],
                    interactive=True
                )
        
        with gr.Column(scale=1):
            with gr.Accordion("Advanced Settings", open=False):
                with gr.Row():
                    size_dropdown = gr.Dropdown(
                        label="Size",
                        choices=SUPPORTED_SIZES,
                        value="832*480",
                        interactive=True
                    )
                    frame_num_slider = gr.Slider(
                        label="Frame Number (4n+1)",
                        minimum=1,
                        maximum=201,
                        step=4,
                        value=81,
                        interactive=True
                    )
                with gr.Row():
                    sample_steps_slider = gr.Slider(
                        label="Sampling Steps",
                        minimum=1,
                        maximum=100,
                        step=1,
                        value=40,
                        interactive=True
                    )
                    sample_solver_dropdown = gr.Dropdown(
                        label="Sample Solver",
                        choices=['unipc', 'dpm++'],
                        value='unipc',
                        interactive=True
                    )
                with gr.Row():
                    sample_shift_slider = gr.Slider(
                        label="Sample Shift",
                        minimum=0,
                        maximum=10,
                        step=0.1,
                        value=5.0,
                        interactive=True
                    )
                    base_seed_number = gr.Number(
                        label="Seed (-1 for random)",
                        value=-1,
                        step=1,
                        interactive=True
                    )

    generate_btn = gr.Button("Generate!", variant="primary")
    
    with gr.Row():
        with gr.Column():
            output_log = gr.Textbox(label="Process Log", lines=10, max_lines=10, interactive=False)
        with gr.Column():
            output_image = gr.Image(label="Generated Image")
            output_video = gr.Video(label="Generated Video")

    # Event handlers
    task_selector.change(
        update_defaults,
        inputs=[task_selector],
        outputs=[size_dropdown, frame_num_slider, sample_steps_slider, sample_solver_dropdown, sample_shift_slider]
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
            base_seed_number
        ],
        outputs=[output_log, output_image, output_video]
    )
    
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)