#!/usr/bin/env python3
"""
Nano Banana Pro - Text-to-Image Generation
Generate images using Gemini 3 Pro Image (Nano Banana)

Requirements:
    pip install google-genai pillow

Usage:
    python generate.py --prompt "A sunset over mountains" --output output.png
    python generate.py --prompt "A cat" --resolution 4K --output cat.png
    python generate.py --prompt "Test" --api-key YOUR_KEY --output test.png
"""

import argparse
import os
import sys
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


def generate_image(prompt: str, api_key: str = None, resolution: str = "2K", output: str = "output.png"):
    """
    Generate an image from a text prompt using Gemini 3 Pro Image.
    
    Args:
        prompt: Text description of the image to generate
        api_key: Gemini API key (can also be set via GEMINI_API_KEY env var)
        resolution: Image resolution (1K, 2K, or 4K)
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
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Get resolution
    size = RESOLUTIONS.get(resolution, RESOLUTIONS["2K"])
    width, height = size.split("x")
    
    print(f"Generating image with Nano Banana Pro...")
    print(f"Prompt: {prompt}")
    print(f"Resolution: {resolution} ({size})")
    
    try:
        # Generate image using Gemini 3 Pro Image
        response = client.models.generate_content(
            model="gemini-3.0-pro-image-preview",  # Nano Banana Pro
            contents=prompt,
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
        import base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save output
        output_path = Path(output)
        image.save(output_path, "PNG")
        
        print(f"✓ Image saved to: {output_path.absolute()}")
        print(f"  Size: {image.size[0]}x{image.size[1]}")
        
    except Exception as e:
        print(f"Error generating image: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with Nano Banana Pro (Gemini 3 Pro Image)"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Text description of the image to generate"
    )
    parser.add_argument(
        "--output", "-o",
        default="output.png",
        help="Output filename (default: output.png)"
    )
    parser.add_argument(
        "--resolution", "-r",
        choices=["1K", "2K", "4K"],
        default="2K",
        help="Image resolution (default: 2K)"
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    # Import here to avoid issues if not needed
    import io
    
    generate_image(
        prompt=args.prompt,
        api_key=args.api_key,
        resolution=args.resolution,
        output=args.output
    )


if __name__ == "__main__":
    main()
