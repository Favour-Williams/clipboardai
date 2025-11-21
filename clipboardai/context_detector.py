"""
Context Detector for ClipboardAI

This module analyzes clipboard content and determines its type,
which allows ClipboardAI to offer relevant actions.

LEARNING FOCUS: Pattern matching, string analysis, decision trees
"""

import re
from typing import Dict, List, Optional
from enum import Enum


# ==============================================================================
# CONTENT TYPES (Using Enum for type safety)
# ==============================================================================

class ContentType(Enum):
    """Enumeration of supported content types."""
    PYTHON_CODE = "python_code"
    JAVASCRIPT_CODE = "javascript_code"
    GIT_DIFF = "git_diff"
    URL = "url"
    EMAIL = "email"
    JSON = "json"
    MARKDOWN = "markdown"
    SQL = "sql"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


# ==============================================================================
# DETECTION RULES (Pattern-based matching)
# ==============================================================================

class ContextDetector:
    """
    Detects the type of content in clipboard using pattern matching.
    
    Detection Strategy:
    1. Check for strong indicators (git diff, URLs)
    2. Check for programming language patterns
    3. Check for structured data (JSON, SQL)
    4. Fall back to plain text
    """
    
    def __init__(self):
        # Compile regex patterns once for performance
        self.url_pattern = re.compile(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
        )
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
    
    def detect(self, content: str) -> Dict:
        """
        Detect content type and return metadata.
        
        Args:
            content (str): The clipboard content to analyze
            
        Returns:
            dict: {
                'type': ContentType,
                'confidence': float (0-1),
                'metadata': dict with type-specific info,
                'suggested_actions': list of action names
            }
        """
        if not content or not content.strip():
            return self._create_result(ContentType.UNKNOWN, 0.0, {}, [])
        
        content = content.strip()
        
        # Priority-based detection (order matters!)
        
        # 1. Git diff (very specific pattern)
        if self._is_git_diff(content):
            return self._create_result(
                ContentType.GIT_DIFF,
                0.95,
                {'lines': content.count('\n')},
                ['generate_commit', 'summarize_changes']
            )
        
        # 2. URL (very specific pattern)
        if self._is_url(content):
            return self._create_result(
                ContentType.URL,
                0.9,
                {'url': content},
                ['fetch_content', 'summarize_page', 'extract_links']
            )
        
        # 3. Programming languages
        lang_result = self._detect_programming_language(content)
        if lang_result:
            return lang_result
        
        # 4. Structured data
        if self._is_json(content):
            return self._create_result(
                ContentType.JSON,
                0.85,
                {},
                ['format_json', 'validate_json', 'extract_values']
            )
        
        if self._is_sql(content):
            return self._create_result(
                ContentType.SQL,
                0.8,
                {},
                ['format_sql', 'explain_query', 'optimize']
            )
        
        # 5. Markdown
        if self._is_markdown(content):
            return self._create_result(
                ContentType.MARKDOWN,
                0.7,
                {},
                ['convert_to_html', 'extract_headings', 'summarize']
            )
        
        # 6. Email
        if self._is_email(content):
            return self._create_result(
                ContentType.EMAIL,
                0.9,
                {},
                ['validate_email']
            )
        
        # 7. Default to plain text
        return self._create_result(
            ContentType.PLAIN_TEXT,
            0.6,
            {'word_count': len(content.split())},
            ['fix_grammar', 'translate', 'summarize', 'extract_keywords']
        )
    
    # ==========================================================================
    # DETECTION METHODS (Pattern matching logic)
    # ==========================================================================
    
    def _is_git_diff(self, content: str) -> bool:
        """Check if content is a git diff."""
        git_indicators = [
            'diff --git',
            'index ',
            '--- a/',
            '+++ b/',
            '@@ -'
        ]
        return any(indicator in content for indicator in git_indicators)
    
    def _is_url(self, content: str) -> bool:
        """Check if content is a URL."""
        # Single line starting with http/https
        lines = content.split('\n')
        if len(lines) == 1:
            return bool(self.url_pattern.match(content))
        return False
    
    def _is_email(self, content: str) -> bool:
        """Check if content is an email address."""
        lines = content.split('\n')
        if len(lines) == 1:
            return bool(self.email_pattern.match(content))
        return False
    
    def _is_json(self, content: str) -> bool:
        """Check if content is JSON."""
        import json
        try:
            json.loads(content)
            return True
        except:
            return False
    
    def _is_sql(self, content: str) -> bool:
        """Check if content is SQL."""
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 
                       'DELETE', 'CREATE', 'DROP', 'ALTER', 'JOIN']
        upper_content = content.upper()
        # Must contain at least 2 SQL keywords
        keyword_count = sum(1 for kw in sql_keywords if kw in upper_content)
        return keyword_count >= 2
    
    def _is_markdown(self, content: str) -> bool:
        """Check if content is Markdown."""
        md_patterns = [
            r'^#{1,6}\s',      # Headers
            r'\[.*?\]\(.*?\)', # Links
            r'\*\*.*?\*\*',    # Bold
            r'^\s*[-*+]\s',    # Lists
            r'```'             # Code blocks
        ]
        matches = sum(1 for pattern in md_patterns 
                     if re.search(pattern, content, re.MULTILINE))
        return matches >= 2
    
    def _detect_programming_language(self, content: str) -> Optional[Dict]:
        """
        Detect if content is code and which language.
        
        Returns result dict or None if not code.
        """
        # Python indicators
        python_patterns = [
            r'\bdef\s+\w+\s*\(',
            r'\bclass\s+\w+',
            r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import',
            r':\s*$',  # Colon at end of line
        ]
        python_score = sum(1 for p in python_patterns 
                          if re.search(p, content, re.MULTILINE))
        
        # JavaScript indicators
        js_patterns = [
            r'\bfunction\s+\w+\s*\(',
            r'\bconst\s+\w+\s*=',
            r'\blet\s+\w+\s*=',
            r'\bvar\s+\w+\s*=',
            r'=>',  # Arrow function
            r'console\.log',
        ]
        js_score = sum(1 for p in js_patterns 
                      if re.search(p, content, re.MULTILINE))
        
        # Determine language based on scores
        if python_score >= 2:
            return self._create_result(
                ContentType.PYTHON_CODE,
                min(0.6 + (python_score * 0.1), 0.95),
                {'language': 'python', 'lines': content.count('\n') + 1},
                ['fix_typos', 'add_docstring', 'generate_tests', 'explain_code']
            )
        
        if js_score >= 2:
            return self._create_result(
                ContentType.JAVASCRIPT_CODE,
                min(0.6 + (js_score * 0.1), 0.95),
                {'language': 'javascript', 'lines': content.count('\n') + 1},
                ['fix_typos', 'add_jsdoc', 'convert_to_typescript', 'explain_code']
            )
        
        return None
    
    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    
    def _create_result(self, content_type: ContentType, confidence: float, 
                       metadata: Dict, actions: List[str]) -> Dict:
        """Create a standardized result dictionary."""
        return {
            'type': content_type,
            'confidence': confidence,
            'metadata': metadata,
            'suggested_actions': actions
        }
    
    def get_action_names(self, content_type: ContentType) -> List[str]:
        """Get all available actions for a content type."""
        action_map = {
            ContentType.PYTHON_CODE: ['fix_typos', 'add_docstring', 'generate_tests', 'explain_code'],
            ContentType.JAVASCRIPT_CODE: ['fix_typos', 'add_jsdoc', 'convert_to_typescript', 'explain_code'],
            ContentType.GIT_DIFF: ['generate_commit', 'summarize_changes'],
            ContentType.URL: ['fetch_content', 'summarize_page', 'extract_links'],
            ContentType.JSON: ['format_json', 'validate_json', 'extract_values'],
            ContentType.SQL: ['format_sql', 'explain_query', 'optimize'],
            ContentType.MARKDOWN: ['convert_to_html', 'extract_headings', 'summarize'],
            ContentType.PLAIN_TEXT: ['fix_grammar', 'translate', 'summarize', 'extract_keywords'],
        }
        return action_map.get(content_type, [])


# ==============================================================================
# TESTING & EXAMPLES
# ==============================================================================

def test_detector():
    """Test the context detector with various inputs."""
    detector = ContextDetector()
    
    test_cases = [
        # (content, expected_type)
        ("def hello():\n    print('world')", ContentType.PYTHON_CODE),
        ("const x = 42;", ContentType.JAVASCRIPT_CODE),
        ("diff --git a/file.py b/file.py", ContentType.GIT_DIFF),
        ("https://example.com", ContentType.URL),
        ('{"name": "John"}', ContentType.JSON),
        ("SELECT * FROM users WHERE id = 1", ContentType.SQL),
        ("# Header\n\nSome **bold** text", ContentType.MARKDOWN),
        ("user@example.com", ContentType.EMAIL),
        ("Just plain text here", ContentType.PLAIN_TEXT),
    ]
    
    print("🧪 Testing Context Detector\n")
    for content, expected in test_cases:
        result = detector.detect(content)
        status = "✅" if result['type'] == expected else "❌"
        print(f"{status} Input: {content[:30]}...")
        print(f"   Detected: {result['type'].value} (confidence: {result['confidence']:.2f})")
        print(f"   Actions: {', '.join(result['suggested_actions'][:3])}")
        print()


if __name__ == "__main__":
    # Run tests
    test_detector()
    
    # Interactive mode
    print("\n" + "="*60)
    print("Interactive Mode: Paste content to detect (Ctrl+C to exit)")
    print("="*60 + "\n")
    
    detector = ContextDetector()
    
    try:
        while True:
            print("Paste your content (press Enter twice to detect):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            
            if not lines:
                continue
            
            content = "\n".join(lines)
            result = detector.detect(content)
            
            print(f"\n📊 Detection Result:")
            print(f"   Type: {result['type'].value}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   Suggested Actions: {', '.join(result['suggested_actions'])}")
            print(f"   Metadata: {result['metadata']}")
            print("\n" + "-"*60 + "\n")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


