#!/bin/bash

# Phantom Video Generation Setup Script
# This script helps you set up and run the Phantom video generation Docker container

echo "🎬 Phantom Video Generation Setup"
echo "=================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if nvidia-docker is available (for GPU support)
if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo "⚠️  GPU support not detected. Running in CPU mode (slower)."
    GPU_SUPPORT=false
else
    echo "✅ GPU support detected."
    GPU_SUPPORT=true
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p outputs uploads examples

# Download example reference images (optional)
echo "📸 Setting up example images..."
if [ ! -f "examples/ref1.png" ]; then
    echo "You can add reference images to the 'examples' folder manually."
fi

# Build Docker image
echo "🔨 Building Docker image..."
echo "This may take several minutes as it downloads models..."

if $GPU_SUPPORT; then
    docker build -t phantom-infer:1.3b .
else
    # Build without GPU optimization
    docker build -t phantom-infer:1.3b-cpu -f Dockerfile.cpu .
fi

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker image built successfully!"

# Function to run the container
run_container() {
    echo "🚀 Starting Phantom Video Generation container..."
    
    if $GPU_SUPPORT; then
        docker run --gpus all \
            -p 7860:7860 \
            -p 8000:8000 \
            -v $(pwd)/outputs:/app/outputs \
            -v $(pwd)/uploads:/app/uploads \
            -v $(pwd)/examples:/app/examples \
            --name phantom-container \
            --rm \
            phantom-infer:1.3b
    else
        docker run \
            -p 7860:7860 \
            -p 8000:8000 \
            -v $(pwd)/outputs:/app/outputs \
            -v $(pwd)/uploads:/app/uploads \
            -v $(pwd)/examples:/app/examples \
            --name phantom-container \
            --rm \
            phantom-infer:1.3b-cpu
    fi
}

# Function to show usage instructions
show_usage() {
    echo ""
    echo "📋 Usage Instructions:"
    echo "====================="
    echo ""
    echo "1. 🌐 Open your browser and go to: http://localhost:7860"
    echo "2. 📝 Enter your text prompt"
    echo "3. 🖼️  (Optional) Upload a reference image"
    echo "4. ⚙️  Adjust settings (resolution, frames, etc.)"
    echo "5. 🎬 Click 'Generate Video'"
    echo "6. ⏳ Wait for generation to complete"
    echo "7. 💾 Download your generated video"
    echo ""
    echo "📁 Output videos are saved to: ./outputs/"
    echo ""
    echo "🔧 Advanced Usage:"
    echo "- API endpoint: http://localhost:8000"
    echo "- API docs: http://localhost:8000/docs"
    echo ""
}

# Main execution
case "${1:-run}" in
    "build")
        echo "✅ Build completed. Run './setup_and_run.sh run' to start the container."
        ;;
    "run")
        show_usage
        echo "Starting container in 5 seconds... (Press Ctrl+C to cancel)"
        sleep 5
        run_container
        ;;
    "help")
        show_usage
        echo "Commands:"
        echo "  ./setup_and_run.sh build  - Only build the Docker image"
        echo "  ./setup_and_run.sh run    - Build and run the container (default)"
        echo "  ./setup_and_run.sh help   - Show this help message"
        ;;
    *)
        show_usage
        run_container
        ;;
esac
