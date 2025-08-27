# import gradio as gr
# import subprocess
# import os
# import shutil
# import random
# import re
# import time
# from PIL import Image

# # Define the tasks and their default settings based on generate.py and README.md
# TASKS = {
#     "s2v-1.3B": {
#         "size": "832*480",
#         "frame_num": 81,
#         "sample_steps": 40,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale_img": 5.0,
#         "guide_scale_text": 7.5
#     },
#     "s2v-14B": {
#         "size": "832*480",
#         "frame_num": 121,
#         "sample_steps": 40,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale_img": 5.0,
#         "guide_scale_text": 7.5
#     },
#     "t2v-1.3B": {
#         "size": "1280*720",
#         "frame_num": 81,
#         "sample_steps": 50,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale": 5.0
#     },
#     "t2v-14B": {
#         "size": "1280*720",
#         "frame_num": 81,
#         "sample_steps": 50,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale": 5.0
#     },
#     "t2i-14B": {
#         "size": "1280*720",
#         "frame_num": 1,
#         "sample_steps": 50,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale": 5.0
#     },
#     "i2v-14B": {
#         "size": "1280*720",
#         "frame_num": 81,
#         "sample_steps": 40,
#         "sample_solver": "unipc",
#         "sample_shift": 3.0,
#         "guide_scale": 5.0
#     }
# }

# SUPPORTED_SIZES = ["1280*720", "720*1280", "832*480", "480*832", "1024*576", "576*1024", "720*480", "480*720", "640*480", "480*640", "1024*1024"]

# def update_defaults(task):
#     config = TASKS.get(task, {})
#     return (
#         config.get("size", "1280*720"),
#         config.get("frame_num", 81),
#         config.get("sample_steps", 50),
#         config.get("sample_solver", "unipc"),
#         config.get("sample_shift", 5.0)
#     )

# def wait_for_file_with_timeout(file_path, timeout=300, check_interval=2):
#     """Wait for file to exist and have reasonable size with timeout"""
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         if os.path.exists(file_path):
#             # Check file size - wait a bit more if file is still being written
#             file_size = os.path.getsize(file_path)
#             if file_size > 1024:  # More than 1KB
#                 # Wait additional 2 seconds to ensure file is completely written
#                 time.sleep(2)
#                 final_size = os.path.getsize(file_path)
#                 if final_size >= file_size:  # File size stable
#                     return True, file_size
#         time.sleep(check_interval)
#     return False, 0

# def find_generated_file(base_path):
#     """Try to find the generated file with different possible extensions and naming"""
#     possible_files = [
#         f"{base_path}.mp4",
#         f"{base_path}.png",
#         base_path,  # Without extension
#     ]
    
#     # Also check for files in the directory with similar base name
#     if os.path.dirname(base_path):
#         dir_path = os.path.dirname(base_path)
#         base_name = os.path.basename(base_path)
#         if os.path.exists(dir_path):
#             for file in os.listdir(dir_path):
#                 if file.startswith(base_name) and (file.endswith('.mp4') or file.endswith('.png')):
#                     possible_files.append(os.path.join(dir_path, file))
    
#     for file_path in possible_files:
#         if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
#             return file_path
    
#     return None

# def generate_video_or_image(
#     task,
#     prompt,
#     ref_images,
#     size,
#     frame_num,
#     sample_steps,
#     sample_solver,
#     sample_shift,
#     base_seed,
# ):
#     if not prompt:
#         raise gr.Error("Prompt cannot be empty.")
    
#     if not os.path.exists("./Wan2.1-T2V-1.3B"):
#         raise gr.Error("Wan2.1-T2V-1.3B model not found. Please run the model download script.")
    
#     if task == "s2v-1.3B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-1.3B.pth"):
#         raise gr.Error("Phantom-Wan-1.3B model not found. Please run the model download script.")
#     elif task == "s2v-14B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-14B.pth"):
#         raise gr.Error("Phantom-Wan-14B model not found. Please run the model download script.")

#     # Sanitize prompt for filename
#     sanitized_prompt = re.sub(r'[^a-zA-Z0-9_ -]', '', prompt).replace(" ", "_").replace("/", "_")[:50]
#     output_dir = "generated_outputs"
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Generate unique base filename without extension
#     timestamp = int(time.time())
#     base_filename = f"{sanitized_prompt}_{timestamp}_{random.randint(100, 999)}"
#     save_file = os.path.join(output_dir, base_filename)
    
#     # Save reference images to a temporary directory
#     ref_image_paths = []
#     if ref_images and "s2v" in task:
#         ref_image_dir = "temp_ref_images"
#         shutil.rmtree(ref_image_dir, ignore_errors=True)
#         os.makedirs(ref_image_dir)
#         for i, img_path in enumerate(ref_images):
#             try:
#                 with Image.open(img_path) as img:
#                     temp_path = os.path.join(ref_image_dir, f"ref_img_{i}.png")
#                     img.save(temp_path)
#                     ref_image_paths.append(temp_path)
#             except Exception as e:
#                 raise gr.Error(f"Error processing reference image {i}: {e}")
    
#     # Construct the command
#     command = [
#         "python", "generate.py",
#         "--task", task,
#         "--prompt", prompt,
#         "--size", size,
#         "--frame_num", str(frame_num),
#         "--sample_steps", str(sample_steps),
#         "--sample_solver", sample_solver,
#         "--sample_shift", str(sample_shift),
#         "--base_seed", str(base_seed),
#         "--ckpt_dir", "./Wan2.1-T2V-1.3B",
#         "--save_file", save_file  # Pass without extension, let generate.py add it
#     ]

#     if "s2v" in task:
#         phantom_ckpt_path = "./Phantom-Wan-Models/Phantom-Wan-1.3B.pth" if "1.3B" in task else "./Phantom-Wan-Models/Phantom-Wan-14B.pth"
#         command.extend(["--phantom_ckpt", phantom_ckpt_path])
#         if ref_image_paths:
#             command.extend(["--ref_image", ",".join(ref_image_paths)])

#     os.environ['MKL_SERVICE_FORCE_INTEL'] = '1'
    
#     # Run the command
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
#     # Stream output to Gradio
#     output_log = []
#     while True:
#         line = process.stdout.readline()
#         if not line and process.poll() is not None:
#             break
#         if line:
#             output_log.append(line.strip())
#             yield "\n".join(output_log), None, None
    
#     stderr = process.stderr.read()
#     if process.returncode != 0:
#         error_msg = f"Error during generation:\nReturn code: {process.returncode}\nSTDERR: {stderr}\nSTDOUT: {chr(10).join(output_log)}"
#         raise gr.Error(error_msg)

#     # Wait for file to be generated and find it
#     yield "\n".join(output_log + ["Waiting for file generation to complete..."]), None, None
    
#     # Try to find the generated file
#     generated_file = find_generated_file(save_file)
    
#     if not generated_file:
#         # Wait with timeout for file to appear
#         expected_ext = ".png" if "t2i" in task else ".mp4"
#         expected_path = f"{save_file}{expected_ext}"
        
#         file_found, file_size = wait_for_file_with_timeout(expected_path, timeout=60)
        
#         if file_found:
#             generated_file = expected_path
#         else:
#             # Final attempt to find any generated file
#             generated_file = find_generated_file(save_file)
            
#             if not generated_file:
#                 # List files in output directory for debugging
#                 debug_info = []
#                 if os.path.exists(output_dir):
#                     files_in_dir = os.listdir(output_dir)
#                     debug_info.append(f"Files in {output_dir}: {files_in_dir}")
                
#                 error_msg = f"Generated file not found after timeout.\n"
#                 error_msg += f"Expected: {expected_path}\n"
#                 error_msg += f"Base path tried: {save_file}\n"
#                 error_msg += "\n".join(debug_info)
#                 error_msg += f"\nGeneration log:\n{chr(10).join(output_log[-10:])}"  # Last 10 lines
#                 raise gr.Error(error_msg)

#     # Validate and prepare return value
#     try:
#         if "t2i" in task:
#             # Validate image file
#             with Image.open(generated_file) as test_img:
#                 test_img.verify()
#             # Reopen for display (verify() can corrupt the image object)
#             with Image.open(generated_file) as display_img:
#                 return_value = gr.Image(value=generated_file, label="Generated Image")
#         else:
#             # Validate video file
#             file_size = os.path.getsize(generated_file)
#             if file_size < 1024:  # Less than 1KB probably corrupted
#                 raise gr.Error(f"Generated video file appears to be corrupted (size: {file_size} bytes)")
            
#             return_value = gr.Video(value=generated_file, label="Generated Video")
        
#     except Exception as e:
#         raise gr.Error(f"Error validating generated file: {e}")
    
#     # Clean up temporary reference images
#     if ref_image_paths:
#         try:
#             shutil.rmtree("temp_ref_images", ignore_errors=True)
#         except:
#             pass  # Ignore cleanup errors
    
#     success_msg = f"Generation completed successfully!\nFile saved: {generated_file}\nFile size: {os.path.getsize(generated_file)} bytes"
#     final_log = output_log + [success_msg]
    
#     return "\n".join(final_log), return_value, None if "t2i" in task else return_value

# with gr.Blocks(title="Phantom-Wan Generator") as demo:
#     gr.Markdown("# 👻 Phantom-Wan: Subject-Consistent Video Generation")
#     gr.Markdown("Generate videos and images with subject consistency using the Phantom-Wan model.")
    
#     with gr.Row():
#         with gr.Column(scale=1):
#             with gr.Group():
#                 task_selector = gr.Dropdown(
#                     label="Task",
#                     choices=list(TASKS.keys()),
#                     value="s2v-1.3B",
#                     interactive=True
#                 )
#                 prompt_input = gr.Textbox(
#                     label="Prompt",
#                     placeholder="Enter your prompt here."
#                 )
                
#                 ref_image_gallery = gr.File(
#                     label="Reference Images (for s2v tasks, up to 4)",
#                     file_count="multiple",
#                     file_types=["image"],
#                     interactive=True
#                 )
        
#         with gr.Column(scale=1):
#             with gr.Accordion("Advanced Settings", open=False):
#                 with gr.Row():
#                     size_dropdown = gr.Dropdown(
#                         label="Size",
#                         choices=SUPPORTED_SIZES,
#                         value="832*480",
#                         interactive=True
#                     )
#                     frame_num_slider = gr.Slider(
#                         label="Frame Number (4n+1)",
#                         minimum=1,
#                         maximum=201,
#                         step=4,
#                         value=81,
#                         interactive=True
#                     )
#                 with gr.Row():
#                     sample_steps_slider = gr.Slider(
#                         label="Sampling Steps",
#                         minimum=1,
#                         maximum=100,
#                         step=1,
#                         value=40,
#                         interactive=True
#                     )
#                     sample_solver_dropdown = gr.Dropdown(
#                         label="Sample Solver",
#                         choices=['unipc', 'dpm++'],
#                         value='unipc',
#                         interactive=True
#                     )
#                 with gr.Row():
#                     sample_shift_slider = gr.Slider(
#                         label="Sample Shift",
#                         minimum=0,
#                         maximum=10,
#                         step=0.1,
#                         value=5.0,
#                         interactive=True
#                     )
#                     base_seed_number = gr.Number(
#                         label="Seed (-1 for random)",
#                         value=-1,
#                         step=1,
#                         interactive=True
#                     )

#     generate_btn = gr.Button("Generate!", variant="primary")
    
#     with gr.Row():
#         with gr.Column():
#             output_log = gr.Textbox(label="Process Log", lines=10, max_lines=10, interactive=False)
#         with gr.Column():
#             output_image = gr.Image(label="Generated Image")
#             output_video = gr.Video(label="Generated Video")

#     # Event handlers
#     task_selector.change(
#         update_defaults,
#         inputs=[task_selector],
#         outputs=[size_dropdown, frame_num_slider, sample_steps_slider, sample_solver_dropdown, sample_shift_slider]
#     )

#     generate_btn.click(
#         fn=generate_video_or_image,
#         inputs=[
#             task_selector,
#             prompt_input,
#             ref_image_gallery,
#             size_dropdown,
#             frame_num_slider,
#             sample_steps_slider,
#             sample_solver_dropdown,
#             sample_shift_slider,
#             base_seed_number
#         ],
#         outputs=[output_log, output_image, output_video]
#     )
    
# if __name__ == "__main__":
#     demo.launch(server_name="0.0.0.0", server_port=7860)

# import gradio as gr
# import subprocess
# import os
# import shutil
# import random
# import re
# import time
# from PIL import Image

# # Define the tasks and their default settings based on generate.py and README.md
# TASKS = {
#     "s2v-1.3B": {
#         "size": "832*480",
#         "frame_num": 81,
#         "sample_steps": 40,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale_img": 5.0,
#         "guide_scale_text": 7.5
#     },
#     "s2v-14B": {
#         "size": "832*480",
#         "frame_num": 121,
#         "sample_steps": 40,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale_img": 5.0,
#         "guide_scale_text": 7.5
#     },
#     "t2v-1.3B": {
#         "size": "1280*720",
#         "frame_num": 81,
#         "sample_steps": 50,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale": 5.0
#     },
#     "t2v-14B": {
#         "size": "1280*720",
#         "frame_num": 81,
#         "sample_steps": 50,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale": 5.0
#     },
#     "t2i-14B": {
#         "size": "1280*720",
#         "frame_num": 1,
#         "sample_steps": 50,
#         "sample_solver": "unipc",
#         "sample_shift": 5.0,
#         "guide_scale": 5.0
#     },
#     "i2v-14B": {
#         "size": "1280*720",
#         "frame_num": 81,
#         "sample_steps": 40,
#         "sample_solver": "unipc",
#         "sample_shift": 3.0,
#         "guide_scale": 5.0
#     }
# }

# SUPPORTED_SIZES = ["1280*720", "720*1280", "832*480", "480*832", "1024*576", "576*1024", "720*480", "480*720", "640*480", "480*640", "1024*1024"]

# def update_defaults(task):
#     config = TASKS.get(task, {})
#     return (
#         config.get("size", "1280*720"),
#         config.get("frame_num", 81),
#         config.get("sample_steps", 50),
#         config.get("sample_solver", "unipc"),
#         config.get("sample_shift", 5.0)
#     )

# def wait_for_file_with_timeout(file_path, timeout=300, check_interval=2):
#     """Wait for file to exist and have reasonable size with timeout"""
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         if os.path.exists(file_path):
#             # Check file size - wait a bit more if file is still being written
#             file_size = os.path.getsize(file_path)
#             if file_size > 1024:  # More than 1KB
#                 # Wait additional 2 seconds to ensure file is completely written
#                 time.sleep(2)
#                 final_size = os.path.getsize(file_path)
#                 if final_size >= file_size:  # File size stable
#                     return True, file_size
#         time.sleep(check_interval)
#     return False, 0

# def find_generated_file(base_path):
#     """Try to find the generated file with different possible extensions and naming"""
#     possible_files = [
#         f"{base_path}.mp4",
#         f"{base_path}.png",
#         base_path,  # Without extension
#     ]
    
#     # Also check for files in the directory with similar base name
#     if os.path.dirname(base_path):
#         dir_path = os.path.dirname(base_path)
#         base_name = os.path.basename(base_path)
#         if os.path.exists(dir_path):
#             for file in os.listdir(dir_path):
#                 if file.startswith(base_name) and (file.endswith('.mp4') or file.endswith('.png')):
#                     possible_files.append(os.path.join(dir_path, file))
    
#     for file_path in possible_files:
#         if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
#             return file_path
    
#     return None

# def generate_video_or_image(
#     task,
#     prompt,
#     ref_images,
#     size,
#     frame_num,
#     sample_steps,
#     sample_solver,
#     sample_shift,
#     base_seed,
# ):
#     if not prompt:
#         raise gr.Error("Prompt cannot be empty.")
    
#     if not os.path.exists("./Wan2.1-T2V-1.3B"):
#         raise gr.Error("Wan2.1-T2V-1.3B model not found. Please run the model download script.")
    
#     if task == "s2v-1.3B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-1.3B.pth"):
#         raise gr.Error("Phantom-Wan-1.3B model not found. Please run the model download script.")
#     elif task == "s2v-14B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-14B.pth"):
#         raise gr.Error("Phantom-Wan-14B model not found. Please run the model download script.")

#     # Sanitize prompt for filename
#     sanitized_prompt = re.sub(r'[^a-zA-Z0-9_ -]', '', prompt).replace(" ", "_").replace("/", "_")[:50]
#     output_dir = "generated_outputs"
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Generate unique base filename without extension
#     timestamp = int(time.time())
#     base_filename = f"{sanitized_prompt}_{timestamp}_{random.randint(100, 999)}"
#     save_file = os.path.join(output_dir, base_filename)
    
#     # Save reference images to a temporary directory
#     ref_image_paths = []
#     if ref_images and "s2v" in task:
#         ref_image_dir = "temp_ref_images"
#         shutil.rmtree(ref_image_dir, ignore_errors=True)
#         os.makedirs(ref_image_dir)
#         for i, img_path in enumerate(ref_images):
#             try:
#                 with Image.open(img_path) as img:
#                     temp_path = os.path.join(ref_image_dir, f"ref_img_{i}.png")
#                     img.save(temp_path)
#                     ref_image_paths.append(temp_path)
#             except Exception as e:
#                 raise gr.Error(f"Error processing reference image {i}: {e}")
    
#     # Construct the command
#     command = [
#         "python", "generate.py",
#         "--task", task,
#         "--prompt", prompt,
#         "--size", size,
#         "--frame_num", str(frame_num),
#         "--sample_steps", str(sample_steps),
#         "--sample_solver", sample_solver,
#         "--sample_shift", str(sample_shift),
#         "--base_seed", str(base_seed),
#         "--ckpt_dir", "./Wan2.1-T2V-1.3B",
#         "--save_file", save_file  # Pass without extension, let generate.py add it
#     ]

#     if "s2v" in task:
#         phantom_ckpt_path = "./Phantom-Wan-Models/Phantom-Wan-1.3B.pth" if "1.3B" in task else "./Phantom-Wan-Models/Phantom-Wan-14B.pth"
#         command.extend(["--phantom_ckpt", phantom_ckpt_path])
#         if ref_image_paths:
#             command.extend(["--ref_image", ",".join(ref_image_paths)])

#     os.environ['MKL_SERVICE_FORCE_INTEL'] = '1'
    
#     # Run the command
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
#     # Stream output to Gradio
#     output_log = []
#     while True:
#         line = process.stdout.readline()
#         if not line and process.poll() is not None:
#             break
#         if line:
#             output_log.append(line.strip())
#             yield "\n".join(output_log), None, None
    
#     stderr = process.stderr.read()
#     if process.returncode != 0:
#         error_msg = f"Error during generation:\nReturn code: {process.returncode}\nSTDERR: {stderr}\nSTDOUT: {chr(10).join(output_log)}"
#         raise gr.Error(error_msg)

#     # Wait for file to be generated and find it
#     yield "\n".join(output_log + ["Waiting for file generation to complete..."]), None, None
    
#     # Determine expected file path based on how generate.py saves files
#     expected_ext = ".png" if "t2i" in task else ".mp4"
#     expected_path = f"{save_file}{expected_ext}"
    
#     # Wait for the specific file that should be generated
#     file_found, file_size = wait_for_file_with_timeout(expected_path, timeout=120)
    
#     if file_found:
#         generated_file = expected_path
#         yield "\n".join(output_log + [f"File found: {generated_file} ({file_size} bytes)"]), None, None
#     else:
#         # Try to find the generated file with different approaches
#         generated_file = find_generated_file(save_file)
        
#         if not generated_file:
#             # List files in output directory for debugging
#             debug_info = []
#             if os.path.exists(output_dir):
#                 files_in_dir = os.listdir(output_dir)
#                 debug_info.append(f"Files in {output_dir}: {files_in_dir}")
            
#             # Also check for recent files
#             recent_files = []
#             try:
#                 for file in os.listdir(output_dir):
#                     file_path = os.path.join(output_dir, file)
#                     if os.path.isfile(file_path):
#                         mtime = os.path.getmtime(file_path)
#                         if time.time() - mtime < 300:  # Files modified in last 5 minutes
#                             recent_files.append(f"{file} ({os.path.getsize(file_path)} bytes)")
#                 if recent_files:
#                     debug_info.append(f"Recent files: {recent_files}")
#             except:
#                 pass
            
#             error_msg = f"Generated file not found after timeout.\n"
#             error_msg += f"Expected: {expected_path}\n"
#             error_msg += f"Base path tried: {save_file}\n"
#             error_msg += "\n".join(debug_info)
#             error_msg += f"\nGeneration log:\n{chr(10).join(output_log[-10:])}"  # Last 10 lines
#             raise gr.Error(error_msg)
#         else:
#             yield "\n".join(output_log + [f"Alternative file found: {generated_file}"]), None, None

#     # Validate file exists and has reasonable size
#     if not os.path.exists(generated_file):
#         raise gr.Error(f"Generated file not found: {generated_file}")
    
#     file_size = os.path.getsize(generated_file)
#     if file_size < 1024:  # Less than 1KB probably corrupted
#         raise gr.Error(f"Generated file appears to be corrupted (size: {file_size} bytes)")
    
#     # Clean up temporary reference images first
#     if ref_image_paths:
#         try:
#             shutil.rmtree("temp_ref_images", ignore_errors=True)
#         except:
#             pass  # Ignore cleanup errors
    
#     success_msg = f"Generation completed successfully!\nFile saved: {generated_file}\nFile size: {file_size} bytes"
#     final_log = output_log + [success_msg]
    
#     # Prepare return values based on task type
#     try:
#         if "t2i" in task:
#             # For image tasks
#             with Image.open(generated_file) as test_img:
#                 test_img.verify()
#             # Final return for image
#             return "\n".join(final_log), generated_file, None
#         else:
#             # For video tasks - return file path directly and let Gradio handle it
#             return "\n".join(final_log), None, generated_file
        
#     except Exception as e:
#         raise gr.Error(f"Error preparing output: {e}")

# with gr.Blocks(title="Phantom-Wan Generator") as demo:
#     gr.Markdown("# 👻 Phantom-Wan: Subject-Consistent Video Generation")
#     gr.Markdown("Generate videos and images with subject consistency using the Phantom-Wan model.")
    
#     with gr.Row():
#         with gr.Column(scale=1):
#             with gr.Group():
#                 task_selector = gr.Dropdown(
#                     label="Task",
#                     choices=list(TASKS.keys()),
#                     value="s2v-1.3B",
#                     interactive=True
#                 )
#                 prompt_input = gr.Textbox(
#                     label="Prompt",
#                     placeholder="Enter your prompt here."
#                 )
                
#                 ref_image_gallery = gr.File(
#                     label="Reference Images (for s2v tasks, up to 4)",
#                     file_count="multiple",
#                     file_types=["image"],
#                     interactive=True
#                 )
        
#         with gr.Column(scale=1):
#             with gr.Accordion("Advanced Settings", open=False):
#                 with gr.Row():
#                     size_dropdown = gr.Dropdown(
#                         label="Size",
#                         choices=SUPPORTED_SIZES,
#                         value="832*480",
#                         interactive=True
#                     )
#                     frame_num_slider = gr.Slider(
#                         label="Frame Number (4n+1)",
#                         minimum=1,
#                         maximum=201,
#                         step=4,
#                         value=81,
#                         interactive=True
#                     )
#                 with gr.Row():
#                     sample_steps_slider = gr.Slider(
#                         label="Sampling Steps",
#                         minimum=1,
#                         maximum=100,
#                         step=1,
#                         value=40,
#                         interactive=True
#                     )
#                     sample_solver_dropdown = gr.Dropdown(
#                         label="Sample Solver",
#                         choices=['unipc', 'dpm++'],
#                         value='unipc',
#                         interactive=True
#                     )
#                 with gr.Row():
#                     sample_shift_slider = gr.Slider(
#                         label="Sample Shift",
#                         minimum=0,
#                         maximum=10,
#                         step=0.1,
#                         value=5.0,
#                         interactive=True
#                     )
#                     base_seed_number = gr.Number(
#                         label="Seed (-1 for random)",
#                         value=-1,
#                         step=1,
#                         interactive=True
#                     )

#     generate_btn = gr.Button("Generate!", variant="primary")
    
#     with gr.Row():
#         with gr.Column():
#             output_log = gr.Textbox(label="Process Log", lines=10, max_lines=10, interactive=False)
#         with gr.Column():
#             output_image = gr.Image(label="Generated Image")
#             output_video = gr.Video(label="Generated Video")

#     # Event handlers
#     task_selector.change(
#         update_defaults,
#         inputs=[task_selector],
#         outputs=[size_dropdown, frame_num_slider, sample_steps_slider, sample_solver_dropdown, sample_shift_slider]
#     )

#     generate_btn.click(
#         fn=generate_video_or_image,
#         inputs=[
#             task_selector,
#             prompt_input,
#             ref_image_gallery,
#             size_dropdown,
#             frame_num_slider,
#             sample_steps_slider,
#             sample_solver_dropdown,
#             sample_shift_slider,
#             base_seed_number
#         ],
#         outputs=[output_log, output_image, output_video]
#     )
    
# if __name__ == "__main__":
#     demo.launch(server_name="0.0.0.0", server_port=7860)
import gradio as gr
import subprocess
import os
import shutil
import random
import re
import time
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

def wait_for_file_with_timeout(file_path, timeout=300, check_interval=2):
    """Wait for file to exist and have reasonable size with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > 1024:  # More than 1KB
                time.sleep(2)  # Wait additional 2 seconds to ensure file is completely written
                final_size = os.path.getsize(file_path)
                if final_size >= file_size:  # File size stable
                    return True, file_size
        time.sleep(check_interval)
    return False, 0

def find_generated_file(base_path):
    """Try to find the generated file with different possible extensions and naming"""
    possible_files = [
        f"{base_path}.mp4",
        base_path,  # Without extension
    ]
    
    # Also check for files in the directory with similar base name
    if os.path.dirname(base_path):
        dir_path = os.path.dirname(base_path)
        base_name = os.path.basename(base_path)
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.startswith(base_name) and file.endswith('.mp4'):
                    possible_files.append(os.path.join(dir_path, file))
    
    for file_path in possible_files:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
            return file_path
    
    return None

def generate_video(
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
        return "Error: Prompt cannot be empty.", None
    
    if not os.path.exists("./Wan2.1-T2V-1.3B"):
        return "Error: Wan2.1-T2V-1.3B model not found. Please run the model download script.", None
    
    if task == "s2v-1.3B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-1.3B.pth"):
        return "Error: Phantom-Wan-1.3B model not found. Please run the model download script.", None
    elif task == "s2v-14B" and not os.path.exists("./Phantom-Wan-Models/Phantom-Wan-14B.pth"):
        return "Error: Phantom-Wan-14B model not found. Please run the model download script.", None

    # Sanitize prompt for filename
    sanitized_prompt = re.sub(r'[^a-zA-Z0-9_ -]', '', prompt).replace(" ", "_").replace("/", "_")[:50]
    output_dir = "generated_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique base filename without extension
    timestamp = int(time.time())
    base_filename = f"{sanitized_prompt}_{timestamp}_{random.randint(100, 999)}"
    save_file = os.path.join(output_dir, base_filename)
    
    # Save reference images to a temporary directory
    ref_image_paths = []
    if ref_images and "s2v" in task:
        ref_image_dir = "temp_ref_images"
        shutil.rmtree(ref_image_dir, ignore_errors=True)
        os.makedirs(ref_image_dir)
        for i, img_path in enumerate(ref_images):
            try:
                with Image.open(img_path) as img:
                    temp_path = os.path.join(ref_image_dir, f"ref_img_{i}.png")
                    img.save(temp_path)
                    ref_image_paths.append(temp_path)
            except Exception as e:
                return f"Error processing reference image {i}: {e}", None
    
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
        "--save_file", save_file  # Pass without extension, let generate.py add it
    ]

    if "s2v" in task:
        phantom_ckpt_path = "./Phantom-Wan-Models/Phantom-Wan-1.3B.pth" if "1.3B" in task else "./Phantom-Wan-Models/Phantom-Wan-14B.pth"
        command.extend(["--phantom_ckpt", phantom_ckpt_path])
        if ref_image_paths:
            command.extend(["--ref_image", ",".join(ref_image_paths)])

    os.environ['MKL_SERVICE_FORCE_INTEL'] = '1'
    
    try:
        # Run the command and capture output
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Generation failed with return code {result.returncode}\n"
            error_msg += f"STDERR: {result.stderr}\n"
            error_msg += f"STDOUT: {result.stdout}"
            return error_msg, None

        # Wait for file to be generated and find it
        expected_path = f"{save_file}.mp4"
        
        # Wait for the specific file that should be generated
        file_found, file_size = wait_for_file_with_timeout(expected_path, timeout=120)
        
        if file_found:
            generated_file = expected_path
        else:
            # Try to find the generated file with different approaches
            generated_file = find_generated_file(save_file)
            
            if not generated_file:
                # List files in output directory for debugging
                debug_info = []
                if os.path.exists(output_dir):
                    files_in_dir = os.listdir(output_dir)
                    debug_info.append(f"Files in {output_dir}: {files_in_dir}")
                
                error_msg = f"Generated file not found after timeout.\n"
                error_msg += f"Expected: {expected_path}\n"
                error_msg += f"Base path tried: {save_file}\n"
                error_msg += "\n".join(debug_info)
                error_msg += f"\nGeneration stdout:\n{result.stdout[-1000:]}"  # Last 1000 chars
                return error_msg, None

        # Validate file exists and has reasonable size
        if not os.path.exists(generated_file):
            return f"Generated file not found: {generated_file}", None
        
        file_size = os.path.getsize(generated_file)
        if file_size < 1024:  # Less than 1KB probably corrupted
            return f"Generated file appears to be corrupted (size: {file_size} bytes)", None
        
        # Clean up temporary reference images
        if ref_image_paths:
            try:
                shutil.rmtree("temp_ref_images", ignore_errors=True)
            except:
                pass  # Ignore cleanup errors
        
        success_msg = f"Generation completed successfully!\n"
        success_msg += f"File saved: {generated_file}\n"
        success_msg += f"File size: {file_size:,} bytes\n"
        success_msg += f"Task: {task}\n"
        success_msg += f"Size: {size}\n"
        success_msg += f"Frames: {frame_num}\n"
        success_msg += f"Steps: {sample_steps}"
        
        return success_msg, generated_file
        
    except subprocess.TimeoutExpired:
        return "Error: Generation timed out after 10 minutes.", None
    except Exception as e:
        return f"Unexpected error during generation: {str(e)}", None

# Create Gradio interface
with gr.Blocks(title="Phantom-Wan Video Generator") as demo:
    gr.Markdown(
        """
        # 👻 Phantom-Wan: Subject-Consistent Video Generation
        Generate videos with subject consistency using the Phantom-Wan model.
        Supports Subject-to-Video (s2v), Text-to-Video (t2v), and Image-to-Video (i2v) generation.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            with gr.Group():
                gr.Markdown("### Main Settings")
                task_selector = gr.Dropdown(
                    label="Task",
                    choices=list(TASKS.keys()),
                    value="s2v-1.3B",
                    interactive=True
                )
                prompt_input = gr.Textbox(
                    label="Prompt",
                    placeholder="Enter your video description here...",
                    lines=3
                )
                
                ref_image_gallery = gr.File(
                    label="Reference Images (for s2v tasks only)",
                    file_count="multiple",
                    file_types=["image"],
                    interactive=True
                )
        
        with gr.Column(scale=1):
            with gr.Accordion("Advanced Settings", open=False):
                with gr.Row():
                    size_dropdown = gr.Dropdown(
                        label="Resolution",
                        choices=SUPPORTED_SIZES,
                        value="832*480",
                        interactive=True
                    )
                    frame_num_slider = gr.Slider(
                        label="Frame Count",
                        minimum=1,
                        maximum=201,
                        step=4,
                        value=81,
                        interactive=True
                    )
                with gr.Row():
                    sample_steps_slider = gr.Slider(
                        label="Sampling Steps",
                        minimum=20,
                        maximum=100,
                        step=1,
                        value=40,
                        interactive=True
                    )
                    sample_solver_dropdown = gr.Dropdown(
                        label="Sampler",
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
                        label="Seed",
                        value=-1,
                        step=1,
                        interactive=True
                    )

    generate_btn = gr.Button(
        "Generate Video!", 
        variant="primary"
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            output_log = gr.Textbox(
                label="Generation Log", 
                lines=12, 
                max_lines=12, 
                interactive=False
            )
        with gr.Column(scale=1):
            output_video = gr.Video(
                label="Generated Video"
            )

    # Event handlers
    task_selector.change(
        update_defaults,
        inputs=[task_selector],
        outputs=[size_dropdown, frame_num_slider, sample_steps_slider, sample_solver_dropdown, sample_shift_slider]
    )

    generate_btn.click(
        fn=generate_video,
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
        outputs=[output_log, output_video],
        show_progress=True
    )
    
    # Add example section
    with gr.Accordion("Examples", open=False):
        gr.Markdown(
            """
            ### Example Prompts:
            
            **Text-to-Video (t2v):**
            - "A majestic golden retriever running through a sunlit meadow, slow motion, cinematic lighting"
            - "Two anthropomorphic cats in boxing gear fighting on a spotlighted stage"
            
            **Subject-to-Video (s2v):**
            - "The subject is dancing gracefully in a ballroom" (requires reference images)
            - "The character is walking down a busy street at sunset" (requires reference images)
            
            **Image-to-Video (i2v):**
            - "The scene comes alive with gentle movement, leaves rustling in the wind"
            """
        )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        share=False,
        show_error=True
    )