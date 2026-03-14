---
name: Desktop-Control
description: The most advanced desktop automation skill for OpenClaw. Provides pixel-perfect mouse control, lightning-fast keyboard input, screen capture, window management, and clipboard operations.
---

# Desktop Control Skill

The most advanced desktop automation skill for OpenClaw. Provides pixel-perfect mouse control, lightning-fast keyboard input, screen capture, window management, and clipboard operations.

## 🎯 Features

### Mouse Control
- `move(x, y)` - Move mouse to coordinates
- `click(x=None, y=None, button='left')` - Click at position or current location
- `double_click(x=None, y=None)` - Double click
- `right_click(x=None, y=None)` - Right click
- `drag(x1, y1, x2, y2, duration=0.5)` - Drag from one point to another
- `scroll(clicks, x=None, y=None)` - Scroll wheel

### Keyboard Control
- `type_text(text, interval=0.1)` - Type text with optional delay
- `press(key, presses=1, interval=0.1)` - Press a key
- `hotkey(*keys)` - Press multiple keys together (e.g., ctrl, c)
- `key_down(key)` - Hold a key down
- `key_up(key)` - Release a key

### Screen Functions
- `screenshot(region=None, filename=None)` - Capture screen or region
- `get_pixel_color(x, y)` - Get color of pixel at coordinates
- `locate_on_screen(image, confidence=0.9)` - Find image on screen
- `locate_all_on_screen(image, confidence=0.9)` - Find all instances of image

### Window Management
- `get_active_window()` - Get currently active window
- `get_window_position(title)` - Get window coordinates
- `set_window_position(title, x, y)` - Move window
- `get_window_size(title)` - Get window dimensions
- `set_window_size(title, width, height)` - Resize window

### Clipboard
- `copy_to_clipboard(text)` - Copy text to clipboard
- `paste_from_clipboard()` - Get text from clipboard

## 🚀 Quick Start

```python
from desktop_control import DesktopController

# Initialize
dc = DesktopController()

# Move and click
dc.move(500, 300)
dc.click()

# Type text
dc.type_text("Hello, World!")

# Take screenshot
img = dc.screenshot(filename="screen.png")

# Keyboard shortcuts
dc.hotkey('ctrl', 'c')  # Copy
dc.hotkey('ctrl', 'v')  # Paste
```

## ⚙️ Configuration

```python
# Custom settings
dc = DesktopController(
    failsafe=True,        # Enable failsafe (mouse to corner stops)
    pause=0.1,           # Default pause between actions
    confidence=0.9       # Default image recognition confidence
)
```

## 🔒 Security & Safety

### Failsafe
Move mouse to any screen corner to immediately stop all automation. This is enabled by default.

### Best Practices
1. Always test with `failsafe=True`
2. Start with slower speeds (`pause=0.5`)
3. Use explicit coordinates when possible
4. Add delays between rapid actions
5. Never automate sensitive operations (passwords, payments)

## ⚠️ Warnings

### Common Pitfalls
1. **Screen resolution changes** - Coordinates are absolute
2. **DPI scaling** - May affect coordinate accuracy
3. **Multiple monitors** - Coordinates span all displays
4. **Failsafe triggering accidentally** - Increase screen border tolerance

### Permission Errors
- Run Python with administrator privileges for some operations
- Some secure applications block automation

## 📦 Dependencies

- PyAutoGUI - Core automation engine
- Pillow - Image processing
- OpenCV (optional) - Image recognition
- PyGetWindow - Window management

Install all:

```bash
pip install pyautogui pillow opencv-python pygetwindow
```

## 📚 Examples

### Basic Automation
```python
dc = DesktopController()

# Open a program (Windows)
dc.hotkey('win', 'r')
dc.type_text('notepad')
dc.press('enter')

# Wait for it to open
import time
time.sleep(1)

# Type something
dc.type_text("Automated with Desktop Control!")
```

### Screenshot and Locate
```python
# Find a button by image
button_location = dc.locate_on_screen('button.png', confidence=0.9)

if button_location:
    # Click the center of the button
    x, y = dc.center(button_location)
    dc.click(x, y)
```

### Window Management
```python
# Get Chrome window position
pos = dc.get_window_position('Google Chrome')

# Move it to top-left
dc.set_window_position('Google Chrome', 0, 0)

# Resize to full screen
width, height = dc.get_screen_size()
dc.set_window_size('Google Chrome', width, height)
```

## 🎓 Advanced Usage

### Image Recognition
```python
# Find all instances of an icon
icons = dc.locate_all_on_screen('icon.png', confidence=0.8)

for icon in icons:
    x, y = dc.center(icon)
    dc.click(x, y)
    time.sleep(0.5)
```

### Custom Pixel Matching
```python
# Find a specific color on screen
pixel = dc.get_pixel_color(100, 100)
print(f"Color at (100,100): {pixel}")

# Search for color in region
matches = dc.locate_on_screen('red_pixel.png', region=(0, 0, 500, 500))
```

### Keyboard Modifiers
```python
# Hold Shift and type
dc.key_down('shift')
dc.type_text("hello")  # Types "HELLO"
dc.key_up('shift')

# Hold Ctrl and click (for multi-select)
dc.key_down('ctrl')
dc.click(100, 100)
dc.click(200, 100)
dc.key_up('ctrl')
```

## 🛠️ Troubleshooting

### Mouse Not Moving
- Check if accessibility permissions are granted
- Try running as administrator
- Verify PyAutoGUI installation

### Image Not Found
- Increase `confidence` threshold
- Ensure image size matches screen scale
- Check if image is actually visible

### Slow Performance
- Reduce screenshot frequency
- Use `region` parameter to limit search area
- Lower `confidence` if high precision not needed

---

Built for OpenClaw - The ultimate desktop automation companion 🦞

**Version:** 1.0.0  
**Author:** @matagul  
**License:** MIT-0
