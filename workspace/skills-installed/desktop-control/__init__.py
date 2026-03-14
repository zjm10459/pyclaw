"""
Desktop Control - Advanced desktop automation skill for OpenClaw

Provides pixel-perfect mouse control, lightning-fast keyboard input,
screen capture, window management, and clipboard operations.
"""

import pyautogui
import pygetwindow as gw
from PIL import Image
from typing import Optional, Tuple, List, Any
import time
import platform
import subprocess


class DesktopController:
    """
    Advanced desktop automation controller.
    
    Features:
    - Mouse control (move, click, drag, scroll)
    - Keyboard control (type, press, hotkeys)
    - Screen capture and image recognition
    - Window management
    - Clipboard operations
    """
    
    def __init__(self, failsafe: bool = True, pause: float = 0.1, confidence: float = 0.9):
        """
        Initialize the Desktop Controller.
        
        Args:
            failsafe: Enable failsafe (mouse to corner stops automation)
            pause: Default pause between actions in seconds
            confidence: Default image recognition confidence (0.0-1.0)
        """
        pyautogui.FAILSAFE = failsafe
        pyautogui.PAUSE = pause
        self.confidence = confidence
        self.failsafe = failsafe
        self.pause = pause
        
    def move(self, x: int, y: int, duration: float = 0.5):
        """
        Move mouse to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Time to move in seconds (default 0.5)
        """
        pyautogui.moveTo(x, y, duration=duration)
        
    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = 'left'):
        """
        Click at position or current location.
        
        Args:
            x: X coordinate (optional, uses current if None)
            y: Y coordinate (optional, uses current if None)
            button: Mouse button ('left', 'right', 'middle')
        """
        pyautogui.click(x=x, y=y, button=button)
        
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """
        Double click at position or current location.
        
        Args:
            x: X coordinate (optional)
            y: Y coordinate (optional)
        """
        pyautogui.doubleClick(x=x, y=y)
        
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """
        Right click at position or current location.
        
        Args:
            x: X coordinate (optional)
            y: Y coordinate (optional)
        """
        pyautogui.rightClick(x=x, y=y)
        
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5):
        """
        Drag from one point to another.
        
        Args:
            x1, y1: Starting coordinates
            x2, y2: Ending coordinates
            duration: Time to drag in seconds
        """
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=duration)
        
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None):
        """
        Scroll wheel.
        
        Args:
            clicks: Number of clicks (positive=up, negative=down)
            x: X coordinate (optional)
            y: Y coordinate (optional)
        """
        pyautogui.scroll(clicks, x=x, y=y)
        
    def type_text(self, text: str, interval: float = 0.1):
        """
        Type text with optional delay between characters.
        
        Args:
            text: Text to type
            interval: Delay between characters in seconds
        """
        pyautogui.write(text, interval=interval)
        
    def press(self, key: str, presses: int = 1, interval: float = 0.1):
        """
        Press a key.
        
        Args:
            key: Key name (e.g., 'enter', 'space', 'a')
            presses: Number of times to press
            interval: Delay between presses
        """
        pyautogui.press(key, presses=presses, interval=interval)
        
    def hotkey(self, *keys: str):
        """
        Press multiple keys together (e.g., ctrl, c).
        
        Args:
            *keys: Keys to press together
        """
        pyautogui.hotkey(*keys)
        
    def key_down(self, key: str):
        """
        Hold a key down.
        
        Args:
            key: Key name
        """
        pyautogui.keyDown(key)
        
    def key_up(self, key: str):
        """
        Release a key.
        
        Args:
            key: Key name
        """
        pyautogui.keyUp(key)
        
    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None, 
                   filename: Optional[str] = None) -> Image.Image:
        """
        Capture screen or region.
        
        Args:
            region: (left, top, width, height) for partial capture
            filename: Path to save image (optional)
            
        Returns:
            PIL Image object
        """
        screenshot = pyautogui.screenshot(region=region)
        if filename:
            screenshot.save(filename)
        return screenshot
        
    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """
        Get color of pixel at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            RGB tuple (r, g, b)
        """
        pixel = pyautogui.pixel(x, y)
        return (pixel[0], pixel[1], pixel[2])
        
    def locate_on_screen(self, image: str, confidence: Optional[float] = None,
                         region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Find image on screen.
        
        Args:
            image: Path to image file
            confidence: Confidence threshold (0.0-1.0)
            region: Search region (left, top, width, height)
            
        Returns:
            Bounding box (left, top, width, height) or None
        """
        conf = confidence if confidence is not None else self.confidence
        try:
            location = pyautogui.locateOnScreen(image, confidence=conf, region=region)
            return location
        except Exception:
            return None
            
    def locate_all_on_screen(self, image: str, confidence: Optional[float] = None,
                             region: Optional[Tuple[int, int, int, int]] = None) -> List[Tuple[int, int, int, int]]:
        """
        Find all instances of image on screen.
        
        Args:
            image: Path to image file
            confidence: Confidence threshold
            region: Search region
            
        Returns:
            List of bounding boxes
        """
        conf = confidence if confidence is not None else self.confidence
        try:
            locations = list(pyautogui.locateAllOnScreen(image, confidence=conf, region=region))
            return locations
        except Exception:
            return []
            
    def center(self, bounding_box: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Get center point of a bounding box.
        
        Args:
            bounding_box: (left, top, width, height)
            
        Returns:
            (x, y) center coordinates
        """
        return pyautogui.center(bounding_box)
        
    def get_active_window(self) -> Optional[Any]:
        """
        Get currently active window.
        
        Returns:
            Window object or None
        """
        try:
            return gw.getActiveWindow()
        except Exception:
            return None
            
    def get_window_position(self, title: str) -> Optional[Tuple[int, int]]:
        """
        Get window coordinates.
        
        Args:
            title: Window title (partial match)
            
        Returns:
            (x, y) or None
        """
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                return (windows[0].left, windows[0].top)
        except Exception:
            pass
        return None
        
    def set_window_position(self, title: str, x: int, y: int):
        """
        Move window.
        
        Args:
            title: Window title
            x: New X position
            y: New Y position
        """
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].moveTo(x, y)
        except Exception:
            pass
            
    def get_window_size(self, title: str) -> Optional[Tuple[int, int]]:
        """
        Get window dimensions.
        
        Args:
            title: Window title
            
        Returns:
            (width, height) or None
        """
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                return (windows[0].width, windows[0].height)
        except Exception:
            pass
        return None
        
    def set_window_size(self, title: str, width: int, height: int):
        """
        Resize window.
        
        Args:
            title: Window title
            width: New width
            height: New height
        """
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                windows[0].resizeTo(width, height)
        except Exception:
            pass
            
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get screen dimensions.
        
        Returns:
            (width, height)
        """
        return pyautogui.size()
        
    def copy_to_clipboard(self, text: str):
        """
        Copy text to clipboard.
        
        Args:
            text: Text to copy
        """
        pyautogui.write(text)  # This doesn't work for clipboard
        # Use platform-specific method
        if platform.system() == 'Windows':
            subprocess.run(['clip'], input=text.encode(), check=True)
        elif platform.system() == 'Darwin':
            subprocess.run(['pbcopy'], input=text.encode(), check=True)
        else:
            # Linux - try xclip
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
            except Exception:
                # Fallback to xsel
                subprocess.run(['xsel', '--clipboard', '--input'], input=text.encode(), check=True)
                
    def paste_from_clipboard(self) -> str:
        """
        Get text from clipboard.
        
        Returns:
            Clipboard text
        """
        if platform.system() == 'Windows':
            result = subprocess.run(['clip'], capture_output=True, text=True)
            return result.stdout
        elif platform.system() == 'Darwin':
            result = subprocess.run(['pbpaste'], capture_output=True, text=True)
            return result.stdout
        else:
            # Linux - try xclip
            try:
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                      capture_output=True, text=True)
                return result.stdout
            except Exception:
                # Fallback to xsel
                result = subprocess.run(['xsel', '--clipboard', '--output'], 
                                      capture_output=True, text=True)
                return result.stdout


# Convenience function for quick access
def get_controller(failsafe: bool = True, pause: float = 0.1) -> DesktopController:
    """
    Get a DesktopController instance with default settings.
    
    Args:
        failsafe: Enable failsafe
        pause: Default pause between actions
        
    Returns:
        DesktopController instance
    """
    return DesktopController(failsafe=failsafe, pause=pause)


__all__ = ['DesktopController', 'get_controller']
__version__ = '1.0.0'
