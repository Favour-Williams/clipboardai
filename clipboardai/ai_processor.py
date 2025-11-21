"""
AI Processor for ClipboardAI

This module handles all AI API calls to OpenAI and Groq.
It takes prompts from PromptManager and returns AI-generated results.

LEARNING FOCUS: API integration, error handling, token management
"""

import os
from typing import Dict, Optional, Literal
from dataclasses import dataclass
from openai import OpenAI
import time


# ==============================================================================
# CONFIGURATION
# ==============================================================================

@dataclass
class AIConfig:
    """Configuration for AI providers."""
    provider: Literal["openai", "groq"] = "openai"
    model: str = "gpt-4o-mini"  # or "llama-3.3-70b-versatile" for Groq
    api_key: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.3  # Lower = more focused, Higher = more creative
    timeout: int = 30  # seconds


# ==============================================================================
# AI PROCESSOR
# ==============================================================================

class AIProcessor:
    """
    Handles AI API calls with error handling and token tracking.
    
    Features:
    - Support for OpenAI and Groq APIs
    - Automatic retries on failure
    - Token usage tracking
    - Response caching (optional)
    - Rate limit handling
    """
    
    def __init__(self, config: AIConfig):
        """
        Initialize AI processor.
        
        Args:
            config: AIConfig with provider settings
        """
        self.config = config
        self.client = None
        self.total_tokens_used = 0
        self.request_count = 0
        self.cache = {}  # Simple response cache
        
        # Initialize API client
        self._init_client()
    
    def _init_client(self):
        """Initialize the OpenAI/Groq client."""
        api_key = self.config.api_key or os.getenv(
            "OPENAI_API_KEY" if self.config.provider == "openai" else "GROQ_API_KEY"
        )
        
        if not api_key:
            raise ValueError(
                f"API key not found. Set {self.config.provider.upper()}_API_KEY "
                f"environment variable or pass api_key in config."
            )
        
        # Both OpenAI and Groq use OpenAI SDK
        base_url = None
        if self.config.provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.config.timeout
        )
        
        print(f"✅ {self.config.provider.upper()} client initialized")
        print(f"   Model: {self.config.model}")
    
    def process(
        self,
        system_prompt: str,
        user_prompt: str,
        use_cache: bool = False,
        max_retries: int = 3
    ) -> Dict:
        """
        Process a prompt through the AI API.
        
        Args:
            system_prompt: The system prompt (AI personality)
            user_prompt: The user prompt (specific task)
            use_cache: Whether to use cached responses
            max_retries: Number of retry attempts on failure
            
        Returns:
            dict: {
                'success': bool,
                'content': str (AI response),
                'tokens_used': int,
                'model': str,
                'error': str (if failed)
            }
        """
        # Check cache first
        cache_key = f"{system_prompt}::{user_prompt}"
        if use_cache and cache_key in self.cache:
            print("💾 Using cached response")
            return self.cache[cache_key]
        
        # Attempt API call with retries
        for attempt in range(max_retries):
            try:
                result = self._call_api(system_prompt, user_prompt)
                
                # Cache successful result
                if use_cache:
                    self.cache[cache_key] = result
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "rate_limit" in error_msg.lower():
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⏳ Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Check if it's the last attempt
                if attempt == max_retries - 1:
                    print(f"❌ Failed after {max_retries} attempts: {error_msg}")
                    return {
                        'success': False,
                        'content': None,
                        'tokens_used': 0,
                        'model': self.config.model,
                        'error': error_msg
                    }
                
                # Retry
                print(f"⚠️  Attempt {attempt + 1} failed: {error_msg}")
                print(f"   Retrying...")
                time.sleep(1)
        
        # Should never reach here, but just in case
        return {
            'success': False,
            'content': None,
            'tokens_used': 0,
            'model': self.config.model,
            'error': 'Max retries exceeded'
        }
    
    def _call_api(self, system_prompt: str, user_prompt: str) -> Dict:
        """
        Make the actual API call.
        
        This is separated so we can retry just this part.
        """
        self.request_count += 1
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Make API call
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        
        # Extract response
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        # Track usage
        self.total_tokens_used += tokens_used
        
        # Log success
        print(f"✨ AI response received ({tokens_used} tokens)")
        
        return {
            'success': True,
            'content': content,
            'tokens_used': tokens_used,
            'model': self.config.model,
            'error': None
        }
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            'total_requests': self.request_count,
            'total_tokens': self.total_tokens_used,
            'avg_tokens_per_request': (
                self.total_tokens_used / self.request_count 
                if self.request_count > 0 else 0
            ),
            'cached_responses': len(self.cache)
        }
    
    def clear_cache(self):
        """Clear response cache."""
        self.cache.clear()
        print("🗑️  Cache cleared")
    
    def estimate_cost(self) -> float:
        """
        Estimate API cost based on tokens used.
        
        Prices (as of 2025):
        - GPT-4o-mini: $0.15 per 1M input tokens, $0.60 per 1M output
        - Groq (Llama): Free tier available
        
        This is a rough estimate assuming 50/50 input/output split.
        """
        if self.config.provider == "groq":
            return 0.0  # Groq has free tier
        
        # Rough estimate for OpenAI (average input/output)
        cost_per_million = 0.375  # Average of input/output
        estimated_cost = (self.total_tokens_used / 1_000_000) * cost_per_million
        
        return estimated_cost


# ==============================================================================
# INTEGRATION WITH PROMPT MANAGER
# ==============================================================================

class ClipboardAIEngine:
    """
    High-level engine that combines PromptManager + AIProcessor.
    
    This is what the Flask API will use!
    """
    
    def __init__(self, prompt_manager, ai_processor: AIProcessor):
        """
        Initialize the engine.
        
        Args:
            prompt_manager: PromptManager instance
            ai_processor: AIProcessor instance
        """
        self.prompt_manager = prompt_manager
        self.ai_processor = ai_processor
    
    def execute_action(
        self,
        action: str,
        content: str,
        **kwargs
    ) -> Dict:
        """
        Execute an action on clipboard content.
        
        This is the main entry point!
        
        Args:
            action: Action name (e.g., "fix_typos")
            content: Clipboard content
            **kwargs: Additional variables (e.g., target_language)
            
        Returns:
            dict with AI response
        """
        try:
            # Get prompts from manager
            prompts = self.prompt_manager.get_full_prompt(
                action, content, **kwargs
            )
            
            # Process through AI
            result = self.ai_processor.process(
                system_prompt=prompts['system'],
                user_prompt=prompts['user']
            )
            
            # Add action metadata
            result['action'] = action
            result['input_length'] = len(content)
            result['output_length'] = len(result['content']) if result['content'] else 0
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'content': None,
                'error': str(e),
                'action': action
            }
    
    def get_stats(self) -> Dict:
        """Get combined statistics."""
        return {
            'ai_stats': self.ai_processor.get_stats(),
            'available_actions': len(self.prompt_manager.list_actions()),
            'estimated_cost': self.ai_processor.estimate_cost()
        }


# ==============================================================================
# TESTING & EXAMPLES
# ==============================================================================

def test_ai_processor():
    """Test the AI processor with a simple example."""
    print("🧪 Testing AI Processor\n")
    
    # Initialize (you'll need API key in environment)
    config = AIConfig(
        provider="groq",  # Changed from "openai"
        model="llama-3.3-70b-versatile",
        temperature=0.3
    )
    
    try:
        processor = AIProcessor(config)
        
        # Test system prompt
        system = """You are a helpful assistant.
Answer concisely and clearly."""
        
        # Test user prompt
        user = "What is 2+2?"
        
        print("Sending test request to AI...")
        result = processor.process(system, user)
        
        if result['success']:
            print(f"\n✅ Success!")
            print(f"Response: {result['content']}")
            print(f"Tokens: {result['tokens_used']}")
        else:
            print(f"\n❌ Failed: {result['error']}")
        
        # Show stats
        print(f"\n📊 Stats:")
        stats = processor.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
    except ValueError as e:
        print(f"⚠️  {e}")
        print("\nTo test, set your API key:")
        print("export OPENAI_API_KEY='your-key-here'")
        print("or")
        print("export GROQ_API_KEY='your-key-here'")


def example_full_integration():
    """Example showing full integration with PromptManager."""
    print("🔗 Full Integration Example\n")
    
    from prompt_manager import PromptManager
    
    try:
        # Initialize components
        prompt_manager = PromptManager()
        ai_config = AIConfig(provider="openai", model="gpt-4o-mini")
        ai_processor = AIProcessor(ai_config)
        
        # Create engine
        engine = ClipboardAIEngine(prompt_manager, ai_processor)
        
        # Test: Fix typos in code
        code = """def calcluate_total(items):
    sum = 0
    for item in itmes:
        sum += item.price
    return sum"""
        
        print("Testing 'fix_typos' action...")
        print(f"Input code:\n{code}\n")
        
        result = engine.execute_action("fix_typos", code)
        
        if result['success']:
            print(f"✅ Fixed code:\n{result['content']}\n")
            print(f"Tokens used: {result['tokens_used']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Show stats
        print(f"\n📊 Engine Stats:")
        stats = engine.get_stats()
        print(f"   Total requests: {stats['ai_stats']['total_requests']}")
        print(f"   Total tokens: {stats['ai_stats']['total_tokens']}")
        print(f"   Estimated cost: ${stats['estimated_cost']:.4f}")
        
    except ValueError as e:
        print(f"⚠️  {e}")


def example_multiple_actions():
    """Example showing multiple different actions."""
    print("🎯 Multiple Actions Example\n")
    
    from prompt_manager import PromptManager
    
    try:
        prompt_manager = PromptManager()
        ai_config = AIConfig(provider="openai", model="gpt-4o-mini")
        ai_processor = AIProcessor(ai_config)
        engine = ClipboardAIEngine(prompt_manager, ai_processor)
        
        # Test different actions
        test_cases = [
            ("fix_typos", "def calcluate(): pass"),
            ("translate", "Hello world", {"target_language": "Spanish"}),
            ("summarize", "This is a long article about AI..." * 10, {"target_length": 20}),
        ]
        
        for action, content, *extra_args in test_cases:
            kwargs = extra_args[0] if extra_args else {}
            print(f"\nTesting: {action}")
            print(f"Input: {content[:40]}...")
            
            result = engine.execute_action(action, content, **kwargs)
            
            if result['success']:
                print(f"✓ Output: {result['content'][:60]}...")
            else:
                print(f"✗ Error: {result['error']}")
        
        # Final stats
        print(f"\n📊 Final Stats:")
        stats = engine.get_stats()
        print(f"   Requests: {stats['ai_stats']['total_requests']}")
        print(f"   Tokens: {stats['ai_stats']['total_tokens']}")
        print(f"   Cost: ${stats['estimated_cost']:.4f}")
        
    except ValueError as e:
        print(f"⚠️  {e}")


if __name__ == "__main__":
    # Choose which example to run:
    
    # 1. Basic AI processor test
    test_ai_processor()
    
    # 2. Full integration with PromptManager (uncomment to run)
    # example_full_integration()
    
    # 3. Multiple actions test (uncomment to run)
    # example_multiple_actions()
