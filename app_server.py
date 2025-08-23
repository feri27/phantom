"""
FastAPI server for Phantom video generation inference
"""
import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
import shutil

app = FastAPI(title="Phantom Video Generation API")

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.post("/generate")
async def generate_video(
    prompt: str = Form(...),
    reference_image: Optional[UploadFile] = File(None),
    resolution: str = Form("512x320"),
    base_seed: int = Form(42),
    model_path: str = Form("models/Phantom-Wan-1.3B"),
    num_frames: int = Form(25),
    fps: int = Form(8)
):
    """Generate video using Phantom model"""
    
    try:
        # Generate unique ID for this request
        request_id = str(uuid.uuid4())
        
        # Handle reference image
        ref_image_path = None
        if reference_image and reference_image.filename:
            ref_image_path = UPLOAD_DIR / f"{request_id}_{reference_image.filename}"
            with open(ref_image_path, "wb") as buffer:
                shutil.copyfileobj(reference_image.file, buffer)
        
        # Prepare output path
        output_path = OUTPUT_DIR / f"{request_id}_output.mp4"
        
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
        
        if ref_image_path:
            cmd.extend(["--reference_image", str(ref_image_path)])
        
        # Run inference
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500, 
                detail=f"Generation failed: {result.stderr}"
            )
        
        # Check if output file exists
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Output video was not generated"
            )
        
        return {
            "status": "success",
            "request_id": request_id,
            "output_path": str(output_path),
            "message": "Video generated successfully"
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Generation timeout - please try with simpler prompt or fewer frames"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@app.get("/download/{request_id}")
async def download_video(request_id: str):
    """Download generated video"""
    output_path = OUTPUT_DIR / f"{request_id}_output.mp4"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename=f"phantom_video_{request_id}.mp4"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Phantom API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
