"""
Vision Tools Template
Source: Agent Studio Reference Implementation
"""
import base64
import os
from typing import Optional
from pydantic_ai import RunContext
from pydantic_deep import DeepAgentDeps


async def analyze_image(
    ctx: RunContext[DeepAgentDeps],
    path: str,
    question: Optional[str] = None
) -> str:
    """Analyze an image file using the multimodal vision model.
    
    This tool reads an image from the workspace and analyzes its contents.
    You can optionally ask a specific question about the image.
    
    Args:
        path: Path to the image file (jpg, png, gif, webp)
        question: Optional specific question about the image
    
    Returns:
        Description and analysis of the image contents
    
    Example usage:
        - analyze_image("/uploads/photo.jpg")
        - analyze_image("/data/screenshot.png", "What buttons are visible?")
    """
    try:
        # Read image bytes from backend
        backend = ctx.deps.backend
        
        # Check if file exists
        file_list = backend.ls_info(os.path.dirname(path) or "/")
        filename = os.path.basename(path)
        if not any(f["name"] == filename for f in file_list):
            return f"Error: Image file not found at {path}"
        
        # Read binary content
        if hasattr(backend, '_read_bytes'):
            image_bytes = backend._read_bytes(path)
        else:
            # Fallback for FilesystemBackend
            full_path = os.path.join(backend._root, path.lstrip("/"))
            with open(full_path, "rb") as f:
                image_bytes = f.read()
        
        # Get file extension
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        mime_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg", 
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        
        if ext not in mime_types:
            return f"Error: Unsupported image format '{ext}'. Supported: jpg, jpeg, png, gif, webp"
        
        mime_type = mime_types[ext]
        
        # Encode to base64
        b64_content = base64.b64encode(image_bytes).decode("utf-8")
        
        # Build analysis prompt
        if question:
            prompt = f"Analyze this image and answer: {question}"
        else:
            prompt = (
                "Analyze this image in detail. Describe:\n"
                "1. Main subjects and objects visible\n"
                "2. Any text or labels present\n"
                "3. Colors, layout, and composition\n"
                "4. Any notable features or patterns"
            )
        
        # Return image info for now (in production, would call vision model)
        file_size = len(image_bytes)
        return (
            f"Image: {path}\n"
            f"Format: {ext.upper()}\n"
            f"Size: {file_size:,} bytes\n"
            f"MIME: {mime_type}\n\n"
            f"[Vision analysis available - delegate to vision subagent for detailed analysis]"
        )
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


async def describe_image(ctx: RunContext[DeepAgentDeps], path: str) -> str:
    """Get a brief description of an image file.
    
    Args:
        path: Path to the image file
        
    Returns:
        Brief description of image contents
    """
    return await analyze_image(ctx, path, "Briefly describe what you see in this image.")


async def extract_text_from_image(ctx: RunContext[DeepAgentDeps], path: str) -> str:
    """Extract any visible text from an image (OCR-like functionality).
    
    Args:
        path: Path to the image file
        
    Returns:
        Text content extracted from the image
    """
    return await analyze_image(ctx, path, "Extract and list all visible text from this image.")
