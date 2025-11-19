"""
ClipboardAI Core - Integration Layer

This module connects the clipboard monitor with context detection
and prepares content for AI processing.

LEARNING FOCUS: System architecture, component integration, event-driven design
"""

import pyperclip
import time
from typing import Dict, Callable, Optional
from enum import Enum

# Import our custom modules
from context_detector import ContextDetector, ContentType


# ==============================================================================
# CLIPBOARD EVENT (Data structure for clipboard changes)
# ==============================================================================

class ClipboardEvent:
    """
    Represents a clipboard change event with detected context.
    
    This is the data structure that flows through ClipboardAI:
    Monitor → Detector → Event → AI Processor
    """
    
    def __init__(self, content: str, detection_result: Dict):
        self.content = content
        self.content_type = detection_result['type']
        self.confidence = detection_result['confidence']
        self.metadata = detection_result['metadata']
        self.suggested_actions = detection_result['suggested_actions']
        self.timestamp = time.time()
    
    def __repr__(self):
        return (f"ClipboardEvent(type={self.content_type.value}, "
                f"confidence={self.confidence:.2f}, "
                f"actions={len(self.suggested_actions)})")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'content': self.content,
            'content_type': self.content_type.value,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'suggested_actions': self.suggested_actions,
            'timestamp': self.timestamp,
            'preview': self.get_preview()
        }
    
    def get_preview(self, max_length: int = 100) -> str:
        """Get a preview of the content for UI display."""
        preview = self.content[:max_length]
        if len(self.content) > max_length:
            preview += "..."
        # Clean up newlines for single-line display
        return preview.replace('\n', ' ↵ ').replace('\r', '')


# ==============================================================================
# CLIPBOARDAI CORE (The main controller)
# ==============================================================================

class ClipboardAI:
    """
    Main ClipboardAI controller that orchestrates all components.
    
    Architecture:
    1. Monitor clipboard for changes
    2. Detect content type when clipboard changes
    3. Fire event with detected context
    4. Allow handlers to process the event
    
    This uses the OBSERVER PATTERN - you can attach multiple handlers
    that get notified when clipboard changes.
    """
    
    def __init__(self, poll_interval: float = 0.5):
        """
        Initialize ClipboardAI.
        
        Args:
            poll_interval: Seconds between clipboard checks
        """
        self.poll_interval = poll_interval
        self.detector = ContextDetector()
        self.handlers = []  # List of callback functions
        self.last_content = None
        self.is_running = False
        self.event_history = []  # Store recent events
        self.max_history = 50  # Keep last 50 events
    
    # ==========================================================================
    # EVENT HANDLER REGISTRATION (Observer Pattern)
    # ==========================================================================
    
    def on_clipboard_change(self, handler: Callable[[ClipboardEvent], None]):
        """
        Register a handler function to be called when clipboard changes.
        
        Args:
            handler: Function that takes a ClipboardEvent as argument
            
        Example:
            def my_handler(event):
                print(f"Detected: {event.content_type}")
            
            app = ClipboardAI()
            app.on_clipboard_change(my_handler)
            app.start()
        """
        self.handlers.append(handler)
        return self  # Allow chaining
    
    def _notify_handlers(self, event: ClipboardEvent):
        """Notify all registered handlers of a clipboard change."""
        for handler in self.handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"⚠️  Handler error: {e}")
    
    # ==========================================================================
    # CLIPBOARD MONITORING (Main loop)
    # ==========================================================================
    
    def start(self):
        """
        Start monitoring the clipboard.
        
        This runs indefinitely until stopped or KeyboardInterrupt.
        """
        self.is_running = True
        print("🚀 ClipboardAI started!")
        print(f"   Polling every {self.poll_interval}s")
        print(f"   Registered handlers: {len(self.handlers)}")
        print("   Press Ctrl+C to stop\n")
        
        try:
            # Get initial clipboard state
            self.last_content = self._get_clipboard_safe()
            
            while self.is_running:
                current_content = self._get_clipboard_safe()
                
                # Check if content changed
                if (current_content is not None and 
                    current_content != self.last_content and
                    current_content.strip()):  # Ignore empty clipboard
                    
                    # Process the new content
                    self._process_clipboard_change(current_content)
                    self.last_content = current_content
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n\n✋ ClipboardAI stopped by user")
            self.stop()
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            self.stop()
    
    def stop(self):
        """Stop the clipboard monitor."""
        self.is_running = False
        print(f"📊 Session summary:")
        print(f"   Events processed: {len(self.event_history)}")
        print("👋 Goodbye!")
    
    # ==========================================================================
    # CLIPBOARD PROCESSING (Core logic)
    # ==========================================================================
    
    def _process_clipboard_change(self, content: str):
        """
        Process a clipboard change by detecting context and firing event.
        
        This is where the magic happens:
        1. Detect what type of content was copied
        2. Create an event with all the metadata
        3. Store in history
        4. Notify all handlers
        """
        # Detect content type
        detection_result = self.detector.detect(content)
        
        # Create event object
        event = ClipboardEvent(content, detection_result)
        
        # Store in history
        self._add_to_history(event)
        
        # Show in console (for debugging)
        self._display_event(event)
        
        # Notify all registered handlers
        self._notify_handlers(event)
    
    def _add_to_history(self, event: ClipboardEvent):
        """Add event to history, maintaining max size."""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)  # Remove oldest
    
    def _display_event(self, event: ClipboardEvent):
        """Display event information in console."""
        confidence_bar = "█" * int(event.confidence * 10)
        confidence_str = f"{confidence_bar:<10} {event.confidence:.0%}"
        
        print(f"📋 Clipboard Event #{len(self.event_history)}")
        print(f"   Type: {event.content_type.value}")
        print(f"   Confidence: {confidence_str}")
        print(f"   Preview: {event.get_preview(60)}")
        print(f"   Actions: {', '.join(event.suggested_actions[:4])}")
        
        # Show metadata if available
        if event.metadata:
            meta_str = ', '.join(f"{k}={v}" for k, v in event.metadata.items())
            print(f"   Metadata: {meta_str}")
        
        print()
    
    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    
    def _get_clipboard_safe(self) -> Optional[str]:
        """Safely get clipboard content with error handling."""
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"⚠️  Error reading clipboard: {e}")
            return None
    
    def get_history(self, limit: int = 10) -> list:
        """Get recent clipboard events."""
        return self.event_history[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
        print("🗑️  History cleared")


# ==============================================================================
# EXAMPLE HANDLERS (Show different ways to use ClipboardAI)
# ==============================================================================

def simple_handler(event: ClipboardEvent):
    """Example: Simple handler that just acknowledges the event."""
    print(f"✨ Handler received: {event.content_type.value}")


def code_focused_handler(event: ClipboardEvent):
    """Example: Handler that only cares about code."""
    if event.content_type in [ContentType.PYTHON_CODE, ContentType.JAVASCRIPT_CODE]:
        print(f"💻 Code detected! Language: {event.metadata.get('language', 'unknown')}")
        print(f"   Lines: {event.metadata.get('lines', '?')}")
        print(f"   Ready for: {', '.join(event.suggested_actions)}")


def stats_handler(event: ClipboardEvent):
    """Example: Handler that tracks statistics."""
    # In a real app, this would update a dashboard
    stats = {
        'total_chars': len(event.content),
        'total_words': len(event.content.split()),
        'type': event.content_type.value,
    }
    print(f"📊 Stats: {stats}")


def ai_ready_handler(event: ClipboardEvent):
    """
    Example: Handler that prepares content for AI processing.
    
    This is what we'll expand later when we add the actual AI integration!
    """
    print(f"🤖 Preparing for AI processing...")
    print(f"   Content type: {event.content_type.value}")
    print(f"   Will use system prompt for: {event.content_type.value}")
    print(f"   Available actions: {event.suggested_actions}")
    print(f"   → Ready to send to OpenAI/Groq!")
    # In next phase, this will actually call the AI API


# ==============================================================================
# USAGE EXAMPLES & TESTING
# ==============================================================================

def example_basic():
    """Basic usage: Just monitor and display."""
    app = ClipboardAI()
    app.start()


def example_with_handlers():
    """Advanced usage: Multiple handlers doing different things."""
    app = ClipboardAI(poll_interval=0.3)  # Faster polling
    
    # Register multiple handlers
    app.on_clipboard_change(simple_handler)
    app.on_clipboard_change(code_focused_handler)
    app.on_clipboard_change(ai_ready_handler)
    
    app.start()


def example_custom_handler():
    """Custom handler that filters by confidence."""
    def high_confidence_only(event: ClipboardEvent):
        if event.confidence >= 0.8:
            print(f"🎯 High confidence detection: {event.content_type.value}")
        else:
            print(f"🤔 Low confidence, might be ambiguous")
    
    app = ClipboardAI()
    app.on_clipboard_change(high_confidence_only)
    app.start()


def test_integration():
    """Test the integration without running the monitor."""
    print("🧪 Testing ClipboardAI Integration\n")
    
    app = ClipboardAI()
    
    # Simulate clipboard changes with test data
    test_cases = [
        "def hello():\n    print('world')",
        "https://github.com",
        "SELECT * FROM users",
        "Just some random text",
    ]
    
    for content in test_cases:
        print(f"Testing: {content[:30]}...")
        detection = app.detector.detect(content)
        event = ClipboardEvent(content, detection)
        app._display_event(event)
        print("-" * 60)


if __name__ == "__main__":
    # Uncomment the example you want to run:
    
    # 1. Basic monitoring (just displays events)
    # example_basic()
    
    # 2. With multiple handlers (shows different use cases)
    example_with_handlers()
    
    # 3. Custom filtered handler
    # example_custom_handler()
    
    # 4. Test without monitoring (for debugging)
    # test_integration()
