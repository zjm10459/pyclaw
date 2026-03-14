#!/usr/bin/env python3
"""
Desktop Control - Demo Script

Demonstrates the capabilities of the Desktop Control skill.
Run this script to see the automation in action!

⚠️  WARNING: This script will control your mouse and keyboard.
    Move your mouse to any screen corner to activate failsafe and stop immediately.
"""

import time
from __init__ import DesktopController


def demo_basic_mouse():
    """Demonstrate basic mouse control."""
    print("\n🖱️  Mouse Control Demo")
    print("=" * 40)
    
    dc = DesktopController(pause=0.5)
    screen_width, screen_height = dc.get_screen_size()
    
    print(f"Screen size: {screen_width}x{screen_height}")
    
    # Move to center
    print("Moving to screen center...")
    dc.move(screen_width // 2, screen_height // 2, duration=1.0)
    time.sleep(1)
    
    # Click
    print("Clicking...")
    dc.click()
    time.sleep(0.5)
    
    # Double click
    print("Double clicking...")
    dc.double_click()
    time.sleep(0.5)
    
    # Right click
    print("Right clicking...")
    dc.right_click()
    time.sleep(0.5)
    
    # Move to corners (but not too fast!)
    print("Moving to corners...")
    dc.move(100, 100, duration=0.5)
    time.sleep(0.3)
    dc.move(screen_width - 100, 100, duration=0.5)
    time.sleep(0.3)
    dc.move(screen_width - 100, screen_height - 100, duration=0.5)
    time.sleep(0.3)
    dc.move(100, screen_height - 100, duration=0.5)
    
    print("✅ Mouse demo complete!")


def demo_keyboard():
    """Demonstrate keyboard control."""
    print("\n⌨️  Keyboard Control Demo")
    print("=" * 40)
    
    dc = DesktopController(pause=0.3)
    
    # Type text
    print("Typing text...")
    dc.type_text("Hello from Desktop Control! ", interval=0.05)
    time.sleep(0.5)
    
    # Press enter
    print("Pressing Enter...")
    dc.press('enter')
    time.sleep(0.5)
    
    # Hotkey example (Ctrl+C to copy)
    print("Demonstrating hotkey (Ctrl+C)...")
    # Note: This won't actually copy anything without text selected
    dc.hotkey('ctrl', 'c')
    time.sleep(0.5)
    
    # Key down/up example
    print("Holding Shift and typing...")
    dc.key_down('shift')
    dc.type_text("this should be uppercase")
    dc.key_up('shift')
    dc.press('enter')
    
    print("✅ Keyboard demo complete!")


def demo_screenshot():
    """Demonstrate screenshot functionality."""
    print("\n📸 Screenshot Demo")
    print("=" * 40)
    
    dc = DesktopController()
    
    # Full screenshot
    print("Taking full screenshot...")
    img = dc.screenshot(filename="demo_full_screenshot.png")
    print(f"Screenshot saved: demo_full_screenshot.png")
    print(f"Image size: {img.size}")
    
    # Region screenshot
    print("Taking region screenshot...")
    screen_width, screen_height = dc.get_screen_size()
    region = (0, 0, screen_width // 2, screen_height // 2)
    img_region = dc.screenshot(region=region, filename="demo_region_screenshot.png")
    print(f"Region screenshot saved: demo_region_screenshot.png")
    print(f"Region size: {img_region.size}")
    
    # Get pixel color
    print("Getting pixel color at center...")
    color = dc.get_pixel_color(screen_width // 2, screen_height // 2)
    print(f"Center pixel color (RGB): {color}")
    
    print("✅ Screenshot demo complete!")


def demo_window_management():
    """Demonstrate window management."""
    print("\n🪟 Window Management Demo")
    print("=" * 40)
    
    dc = DesktopController()
    
    # Get active window
    print("Getting active window...")
    active_window = dc.get_active_window()
    if active_window:
        print(f"Active window: {active_window.title}")
        print(f"Position: ({active_window.left}, {active_window.top})")
        print(f"Size: {active_window.width}x{active_window.height}")
    else:
        print("No active window found")
    
    # Get screen size
    screen_width, screen_height = dc.get_screen_size()
    print(f"Screen size: {screen_width}x{screen_height}")
    
    print("✅ Window management demo complete!")


def demo_safe_mode():
    """Demonstrate safe mode with longer pauses."""
    print("\n🛡️  Safe Mode Demo (slower, safer)")
    print("=" * 40)
    
    # Use slower settings for safety
    dc = DesktopController(failsafe=True, pause=1.0)
    
    print("Safe mode enabled - all actions will be slower")
    print("Move mouse to corner to test failsafe...")
    time.sleep(2)
    
    # Slow movement
    screen_width, screen_height = dc.get_screen_size()
    dc.move(screen_width // 4, screen_height // 2, duration=2.0)
    time.sleep(1)
    dc.move(3 * screen_width // 4, screen_height // 2, duration=2.0)
    
    print("✅ Safe mode demo complete!")
    print("💡 Remember: Move mouse to any corner to activate failsafe!")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("🦞 Desktop Control - Demo Suite")
    print("=" * 60)
    print("\n⚠️  SAFETY WARNING:")
    print("   - This script will control your mouse and keyboard")
    print("   - Move mouse to ANY screen corner to activate FAILSAFE")
    print("   - Failsafe will immediately stop all automation")
    print("\nStarting in 5 seconds... Move mouse to corner to abort!")
    
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    try:
        demo_basic_mouse()
        time.sleep(1)
        
        demo_keyboard()
        time.sleep(1)
        
        demo_screenshot()
        time.sleep(1)
        
        demo_window_management()
        time.sleep(1)
        
        demo_safe_mode()
        
        print("\n" + "=" * 60)
        print("🎉 All demos completed successfully!")
        print("=" * 60)
        print("\n📚 Next steps:")
        print("   - Check SKILL.md for full documentation")
        print("   - Try the examples in QUICK_REFERENCE.md")
        print("   - Start building your own automation scripts!")
        
    except pyautogui.FailSafeException:
        print("\n🛑 FAILSAFE ACTIVATED!")
        print("   Automation stopped safely.")
        print("   This is expected behavior when mouse moves to corner.")
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
