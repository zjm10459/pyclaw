#!/usr/bin/env python3
"""
Nano Banana Pro - Image-to-Image Editing
Edit images using Gemini 3 Pro Image (Nano Banana)

Requirements:
    pip install google-genai pillow

Usage:
    python edit.py --input-image input.png --prompt "Add sunglasses" --output edited.png
    python edit.py -i photo.jpg -p "Remove background" -o result.png
"""

import argparse
import os
import sys
import base64
import io
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not installed.")
    print("Install with: pip install google-genai")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: pillow package not installed.")
    print("Install with: pip install pillow")
    sys.exit(1)


# Resolution mapping
RESOLUTIONS = {
    "1K": "1024x1024",
    "2K": "2048x2048",
    "4K": "4096x4096",
}


def edit_image(input_image: str, prompt: str, api_key: str = None, 
               resolution: str = "2K", output: str = "edited.png"):
    """
    Edit an image using Gemini 3 Pro Image.
    
    Args:
        input_image: Path to the input image
        prompt: Text description of the edit to perform
        api_key: Gemini API key (can also be set via GEMINI_API_KEY env var)
        resolution: Output image resolution (1K, 2K, or 4K)
        output: Output filename
    """
    # Get API key
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: No API key provided.")
        print("Set GEMINI_API_KEY environment variable or use --api-key option.")
        print("Get your API key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    # Check input image exists
    input_path = Path(input_image)
    if not input_path.exists():
        print(f"Error: Input image not found: {input_path}")
        sys.exit(1)
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Get resolution
    size = RESOLUTIONS.get(resolution, RESOLUTIONS["2K"])
    width, height = size.split("x")
    
    print(f"Editing image with Nano Banana Pro...")
    print(f"Input: {input_path.absolute()}")
    print(f"Prompt: {prompt}")
    print(f"Resolution: {resolution} ({size})")
    
    try:
        # Load and encode input image
        with open(input_path, "rb") as f:
            image_bytes = f.read()
        
        # Create image part for the request
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png" if input_path.suffix == ".png" else "image/jpeg"
        )
        
        # Combine prompt and image
        contents = [
            image_part,
            prompt
        ]
        
        # Generate edited image
        response = client.models.generate_content(
            model="gemini-3.0-pro-image-preview",  # Nano Banana Pro
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
        )
        
        # Extract image from response
        image_data = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'image') and part.image:
                image_data = part.image.data
                break
            elif hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                break
        
        if not image_data:
            print("Error: No image data in response")
            print(f"Response: {response}")
            sys.exit(1)
        
        # Convert to PIL Image and save
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save output
        output_path = Path(output)
        image.save(output_path, "PNG")
        
        print(f"✓ Edited image saved to: {output_path.absolute()}")
        print(f"  Size: {image.size[0]}x{image.size[1]}")
        
    except Exception as e:
        print(f"Error editing image: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Edit images with Nano Banana Pro (Gemini 3 Pro Image)"
    )
    parser.add_argument(
        "--input-image", "-i",
        required=True,
        help="Path to the input image"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Text description of the edit to perform"
    )
    parser.add_argument(
        "--output", "-o",
        default="edited.png",
        help="Output filename (default: edited.png)"
    )
    parser.add_argument(
        "--resolution", "-r",
        choices=["1K", "2K", "4K"],
        default="2K",
        help="Output image resolution (default: 2K)"
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    edit_image(
        input_image=args.input_image,
        prompt=args.prompt,
        api_key=args.api_key,
        resolution=args.resolution,
        output=args.output
    )


if __name__ == "__main__":
    main()
