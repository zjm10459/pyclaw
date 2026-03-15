---
name: nano-banana-pro
description: "Generate/edit images with Nano Banana Pro (Gemini 3 Pro Image). Supports text-to-image + image-to-image; 1K/2K/4K; use --input-image."
allowed-tools: Bash, Read, Write
metadata: {"clawdbot":{"requires":{"env":["GEMINI_API_KEY"]},"primaryEnv":"GEMINI_API_KEY"}}
---

# Nano Banana Pro

Generate and edit images with Nano Banana Pro (Gemini 3 Pro Image). Supports text-to-image and image-to-image generation with 1K/2K/4K resolutions.

## Requirements

- Python 3.10+
- `uv` package runner
- `google-genai` package
- `pillow` package
- `GEMINI_API_KEY` environment variable

## Installation

```bash
# Install dependencies
pip install google-genai pillow
# or using uv
uv pip install google-genai pillow
```

## Usage

### Text-to-Image Generation

```bash
# Basic usage
python scripts/generate.py --prompt "A sunset over mountains" --output output.png

# With resolution (1K, 2K, 4K)
python scripts/generate.py --prompt "A cat playing with yarn" --resolution 4K --output cat.png

# With API key
python scripts/generate.py --prompt "A beautiful landscape" --api-key YOUR_API_KEY --output landscape.png
```

### Image-to-Image Editing

```bash
# Edit an existing image
python scripts/edit.py --input-image input.png --prompt "Add sunglasses to the person" --output edited.png

# Background replacement
python scripts/edit.py --input-image photo.png --prompt "Remove background and add sunset" --output photo_edited.png

# Style transfer
python scripts/edit.py --input-image photo.png --prompt "Convert to anime style" --output anime.png
```

## Resolution Options

| Resolution | Dimensions | Use Case |
|------------|------------|----------|
| 1K | 1024x1024 | Quick previews, thumbnails |
| 2K | 2048x2048 | Standard quality images |
| 4K | 4096x4096 | High-quality, detailed images |

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
  - Get your API key at: https://aistudio.google.com/app/apikey

## Examples

### Generate a landscape image
```bash
python scripts/generate.py \
  --prompt "A serene mountain lake at sunrise, reflection in water, photorealistic, 8k" \
  --resolution 4K \
  --output mountain_lake.png
```

### Edit a portrait
```bash
python scripts/edit.py \
  --input-image portrait.jpg \
  --prompt "Make the person smile, add warm lighting" \
  --output portrait_edited.png
```

### Create concept art
```bash
python scripts/generate.py \
  --prompt "Cyberpunk city street at night, neon lights, rain, futuristic cars, cinematic" \
  --resolution 2K \
  --output cyberpunk_city.png
```

## Notes

- Output files are saved as PNG format
- Generation time varies by resolution (1K: ~5s, 2K: ~10s, 4K: ~20s)
- API usage is billed according to Google's pricing
- For best results, use detailed, descriptive prompts
