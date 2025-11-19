# Clipboard watching logic
# algorithm 
# 1. Store the CURRENT clipboard content in a variable (e.g., "last_value")
# 2. Wait 0.5 seconds
# 3. Get the CURRENT clipboard content (e.g., "current_value")
# 4. Compare: Is current_value DIFFERENT from last_value?
#    - If YES → Something new was copied! Process it.
#    - If NO → Nothing changed, keep waiting
# 5. Update last_value to be current_value
# 6. Go back to step 2 (loop forever)


# def clip():
#     last_value = ""
#     while True:
#         current_value = pyperclip.paste()
#         if current_value != last_value:
#             print("Clipboard changed!")
#             print(f"Clipboard changed: {current_value[:50]}...")  # Show first 50 chars
#         last_value = current_value
#         time.sleep(0.5)

import pyperclip
import time
import sys


class ClipboardMonitor:
    """
    Monitors clipboard for changes and triggers a callback when content changes.
    
    This class provides a robust clipboard monitoring solution with:
    - Change detection with configurable polling interval
    - Error handling for clipboard access issues
    - Graceful shutdown on KeyboardInterrupt
    - Callback pattern for extensibility
    """
    
    def __init__(self, poll_interval=0.5, callback=None):
        """
        Initialize the clipboard monitor.
        
        Args:
            poll_interval (float): Seconds between clipboard checks (default: 0.5)
            callback (callable): Function to call when clipboard changes.
                                 Receives clipboard content as argument.
        """
        self.poll_interval = poll_interval
        self.callback = callback or self._default_callback
        self.last_value = None  # Use None instead of "" to detect first copy
        self.is_running = False
    
    def _default_callback(self, content):
        """Default callback that prints clipboard changes."""
        preview = content[:50] + "..." if len(content) > 50 else content
        # Replace newlines for cleaner output
        preview = preview.replace('\n', '\\n').replace('\r', '\\r')
        print(f"📋 Clipboard changed: {preview}")
    
    def _get_clipboard_safe(self):
        """
        Safely get clipboard content with error handling.
        
        Returns:
            str: Clipboard content, or None if error occurs
        """
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"⚠️  Error reading clipboard: {e}")
            return None
    
    def start(self):
        """
        Start monitoring the clipboard.
        
        Runs indefinitely until KeyboardInterrupt (Ctrl+C).
        """
        self.is_running = True
        print(f"🚀 ClipboardMonitor started (polling every {self.poll_interval}s)")
        print("   Press Ctrl+C to stop\n")
        
        try:
            # Get initial clipboard state
            self.last_value = self._get_clipboard_safe()
            
            while self.is_running:
                current_value = self._get_clipboard_safe()
                
                # Only process if we got valid content and it changed
                if current_value is not None and current_value != self.last_value:
                    # Skip empty clipboard (sometimes happens during copy operations)
                    if current_value.strip():
                        self.callback(current_value)
                    
                    self.last_value = current_value
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n\n✋ ClipboardMonitor stopped by user")
            self.stop()
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the clipboard monitor."""
        self.is_running = False
        print("👋 Goodbye!")
def custom_callback(content):
    """Example: Custom callback that does something useful."""
    print(f"✨ Custom action: Processing {len(content)} characters...")
    
    # Example: Detect content type
    if content.startswith('http'):
        print("   → Detected URL")
    elif 'def ' in content or 'class ' in content:
        print("   → Detected Python code")
    elif content.startswith('diff --git'):
        print("   → Detected Git diff")
    else:
        print("   → Detected text")


if __name__ == "__main__":
    # Example 1: Basic usage with default callback
    monitor = ClipboardMonitor()
    monitor.start()
    
    # Example 2: With custom callback (uncomment to use)
    # monitor = ClipboardMonitor(callback=custom_callback)
    # monitor.start()
    
    # Example 3: With faster polling (uncomment to use)
    # monitor = ClipboardMonitor(poll_interval=0.2)
    # monitor.start()