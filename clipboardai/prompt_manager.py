"""
Prompt Manager for ClipboardAI

This module stores and manages all system prompts for different actions.
Each action has a tailored AI personality defined here.

LEARNING FOCUS: Prompt engineering architecture, separation of concerns
"""

from typing import Dict, Optional, List
from enum import Enum
import json


# ==============================================================================
# ACTION DEFINITIONS (All available actions)
# ==============================================================================

class Action(Enum):
    """Enumeration of all ClipboardAI actions."""
    # Code actions
    FIX_TYPOS = "fix_typos"
    ADD_DOCSTRING = "add_docstring"
    GENERATE_TESTS = "generate_tests"
    EXPLAIN_CODE = "explain_code"
    ADD_JSDOC = "add_jsdoc"
    CONVERT_TO_TYPESCRIPT = "convert_to_typescript"
    
    # Git actions
    GENERATE_COMMIT = "generate_commit"
    SUMMARIZE_CHANGES = "summarize_changes"
    
    # Data actions
    FORMAT_JSON = "format_json"
    VALIDATE_JSON = "validate_json"
    FORMAT_SQL = "format_sql"
    EXPLAIN_QUERY = "explain_query"
    
    # Text actions
    FIX_GRAMMAR = "fix_grammar"
    TRANSLATE = "translate"
    SUMMARIZE = "summarize"
    EXTRACT_KEYWORDS = "extract_keywords"
    
    # Web actions
    SUMMARIZE_PAGE = "summarize_page"
    EXTRACT_LINKS = "extract_links"


# ==============================================================================
# SYSTEM PROMPTS (The AI personalities)
# ==============================================================================

SYSTEM_PROMPTS: Dict[str, str] = {
    
    # -------------------------------------------------------------------------
    # CODE ACTIONS
    # -------------------------------------------------------------------------
    
    Action.FIX_TYPOS.value: """You are a strict code typo fixer.
Only correct spelling or syntax mistakes.
Do not change logic, structure, formatting, or variable names.
Do not add comments or explanations.
Return only the corrected code.""",

    Action.ADD_DOCSTRING.value: """You are a Python documentation expert.
Add clear, concise docstrings following Google style guide.
Include:
- Brief description (one line)
- Args: parameter descriptions
- Returns: return value description
Do NOT modify the code logic itself.
Return the complete function with docstring added.""",

    Action.GENERATE_TESTS.value: """You are a Python testing expert using pytest.
Generate comprehensive unit tests for the provided code.
Include:
- Happy path tests
- Edge cases
- Error conditions
Use clear test names and assertions.
Return complete, runnable test code.""",

    Action.EXPLAIN_CODE.value: """You are a patient code instructor.
Explain the provided code in simple terms.
Include:
- What the code does (overall purpose)
- How it works (step-by-step)
- Key concepts used
Use analogies when helpful.
Be concise but thorough.""",

    Action.ADD_JSDOC.value: """You are a JavaScript documentation expert.
Add clear JSDoc comments following standard conventions.
Include @param, @returns, and @description tags.
Do NOT modify the code logic.
Return the complete function with JSDoc added.""",

    Action.CONVERT_TO_TYPESCRIPT.value: """You are a TypeScript conversion specialist.
Convert the JavaScript code to TypeScript.
Add appropriate type annotations for:
- Function parameters
- Return types
- Variables where helpful
Keep the logic identical, only add types.
Return valid TypeScript code.""",

    # -------------------------------------------------------------------------
    # GIT ACTIONS
    # -------------------------------------------------------------------------
    
    Action.GENERATE_COMMIT.value: """You are CommitBot, a professional Git commit message generator.
Follow Conventional Commits specification strictly.
Use these types: feat, fix, docs, refactor, test, chore, style.
Format: <type>: <description>
Use present tense, imperative mood.
Keep description under 72 characters.
Do NOT add body or footer unless changes are complex.
Output only the commit message.""",

    Action.SUMMARIZE_CHANGES.value: """You are a code review assistant.
Summarize the git diff in plain English.
Include:
- What was changed (files/functions)
- Why it matters (impact)
- Any potential concerns
Be concise. Use bullet points.
Aim for 3-5 sentences maximum.""",

    # -------------------------------------------------------------------------
    # DATA ACTIONS
    # -------------------------------------------------------------------------
    
    Action.FORMAT_JSON.value: """You are a JSON formatter.
Format the provided JSON with proper indentation.
Use 2 spaces for indentation.
Ensure valid JSON syntax.
Do NOT modify the data, only format it.
Return formatted JSON only.""",

    Action.VALIDATE_JSON.value: """You are a JSON validator.
Check if the provided JSON is valid.
If valid: respond with "✓ Valid JSON"
If invalid: explain the error clearly and show where it occurs.
Be helpful and specific.""",

    Action.FORMAT_SQL.value: """You are a SQL formatter.
Format the SQL query with proper indentation and capitalization.
- Keywords in UPPERCASE
- Proper line breaks for readability
- Consistent indentation
Return formatted SQL only.""",

    Action.EXPLAIN_QUERY.value: """You are a SQL expert.
Explain what the SQL query does in plain English.
Include:
- What data it retrieves/modifies
- Which tables are involved
- Any joins or filters applied
Be clear and concise.""",

    # -------------------------------------------------------------------------
    # TEXT ACTIONS
    # -------------------------------------------------------------------------
    
    Action.FIX_GRAMMAR.value: """You are a grammar correction specialist.
Fix grammar, spelling, and punctuation errors.
Maintain the original tone and style.
Do NOT rewrite sentences unless grammatically necessary.
Return corrected text only.""",

    Action.TRANSLATE.value: """You are a professional translator.
Translate the text to {target_language}.
Maintain the tone and meaning.
Use natural, fluent language in the target language.
Return only the translation.""",

    Action.SUMMARIZE.value: """You are a summarization expert.
Summarize the text concisely while preserving key information.
Target length: {target_length} words.
Focus on main ideas and important details.
Use clear, simple language.
Return summary only.""",

    Action.EXTRACT_KEYWORDS.value: """You are a keyword extraction specialist.
Extract the most important keywords and phrases from the text.
Return 5-10 keywords/phrases in order of importance.
Format as a comma-separated list.
Focus on meaningful terms, not common words.""",

    # -------------------------------------------------------------------------
    # WEB ACTIONS
    # -------------------------------------------------------------------------
    
    Action.SUMMARIZE_PAGE.value: """You are a web content summarizer.
Summarize the webpage content concisely.
Include:
- Main topic/purpose
- Key points (3-5 bullet points)
- Target audience if evident
Be objective and informative.""",

    Action.EXTRACT_LINKS.value: """You are a link extraction specialist.
Extract all URLs from the content.
Format as a numbered list.
Include brief context for each link if available.
Remove duplicates.""",
}


# ==============================================================================
# USER PROMPT TEMPLATES (Dynamic prompts with variables)
# ==============================================================================

USER_PROMPT_TEMPLATES: Dict[str, str] = {
    Action.FIX_TYPOS.value: "Fix typos in this code:\n\n{content}",
    
    Action.ADD_DOCSTRING.value: "Add a docstring to this function:\n\n{content}",
    
    Action.GENERATE_TESTS.value: "Generate pytest unit tests for this code:\n\n{content}",
    
    Action.EXPLAIN_CODE.value: "Explain this code:\n\n{content}",
    
    Action.GENERATE_COMMIT.value: "Generate a commit message for this diff:\n\n{content}",
    
    Action.SUMMARIZE_CHANGES.value: "Summarize these code changes:\n\n{content}",
    
    Action.FORMAT_JSON.value: "{content}",  # No instruction needed, system prompt handles it
    
    Action.VALIDATE_JSON.value: "{content}",
    
    Action.FORMAT_SQL.value: "{content}",
    
    Action.EXPLAIN_QUERY.value: "Explain this SQL query:\n\n{content}",
    
    Action.FIX_GRAMMAR.value: "{content}",
    
    Action.TRANSLATE.value: "Translate to {target_language}:\n\n{content}",
    
    Action.SUMMARIZE.value: "Summarize in about {target_length} words:\n\n{content}",
    
    Action.EXTRACT_KEYWORDS.value: "Extract keywords from:\n\n{content}",
    
    Action.SUMMARIZE_PAGE.value: "Summarize this webpage:\n\n{content}",
    
    Action.EXTRACT_LINKS.value: "Extract all links from:\n\n{content}",
}


# ==============================================================================
# PROMPT MANAGER CLASS
# ==============================================================================

class PromptManager:
    """
    Manages system prompts and user prompt templates.
    
    This is the central place where all AI personalities are defined.
    Separating prompts from logic makes them easy to:
    - Update and refine
    - A/B test different versions
    - Localize for different languages
    - Version control
    """
    
    def __init__(self, custom_prompts: Optional[Dict[str, str]] = None):
        """
        Initialize the prompt manager.
        
        Args:
            custom_prompts: Optional dictionary to override default prompts
        """
        self.system_prompts = SYSTEM_PROMPTS.copy()
        self.user_templates = USER_PROMPT_TEMPLATES.copy()
        
        if custom_prompts:
            self.system_prompts.update(custom_prompts)
    
    def get_system_prompt(self, action: str) -> str:
        """
        Get system prompt for an action.
        
        Args:
            action: The action name (e.g., "fix_typos")
            
        Returns:
            System prompt string
            
        Raises:
            ValueError: If action not found
        """
        if action not in self.system_prompts:
            raise ValueError(f"No system prompt found for action: {action}")
        
        return self.system_prompts[action].strip()
    
    def get_user_prompt(self, action: str, content: str, **kwargs) -> str:
        """
        Generate user prompt from template.
        
        Args:
            action: The action name
            content: The clipboard content
            **kwargs: Additional variables for template (e.g., target_language)
            
        Returns:
            Formatted user prompt
        """
        if action not in self.user_templates:
            raise ValueError(f"No user template found for action: {action}")
        
        template = self.user_templates[action]
        
        # Merge content with any additional kwargs
        variables = {'content': content, **kwargs}
        
        return template.format(**variables)
    
    def get_full_prompt(self, action: str, content: str, **kwargs) -> Dict[str, str]:
        """
        Get both system and user prompts ready for API call.
        
        Args:
            action: The action name
            content: The clipboard content
            **kwargs: Additional variables
            
        Returns:
            dict with 'system' and 'user' keys
        """
        return {
            'system': self.get_system_prompt(action),
            'user': self.get_user_prompt(action, content, **kwargs)
        }
    
    def list_actions(self) -> List[str]:
        """Get list of all available actions."""
        return list(self.system_prompts.keys())
    
    def save_custom_prompt(self, action: str, system_prompt: str):
        """
        Save a custom system prompt for an action.
        
        This allows users to customize AI behavior!
        """
        self.system_prompts[action] = system_prompt
    
    def export_prompts(self, filepath: str):
        """Export all prompts to JSON file."""
        data = {
            'system_prompts': self.system_prompts,
            'user_templates': self.user_templates
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Prompts exported to {filepath}")
    
    def import_prompts(self, filepath: str):
        """Import prompts from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if 'system_prompts' in data:
            self.system_prompts.update(data['system_prompts'])
        if 'user_templates' in data:
            self.user_templates.update(data['user_templates'])
        
        print(f"✅ Prompts imported from {filepath}")


# ==============================================================================
# TESTING & EXAMPLES
# ==============================================================================

def test_prompt_manager():
    """Test the prompt manager functionality."""
    print("🧪 Testing Prompt Manager\n")
    
    manager = PromptManager()
    
    # Test 1: Get system prompt
    print("Test 1: Getting system prompt for 'fix_typos'")
    system = manager.get_system_prompt("fix_typos")
    print(f"✓ System prompt: {system[:50]}...\n")
    
    # Test 2: Get user prompt
    print("Test 2: Generating user prompt")
    code = "def calcluate_total(items):\n    return sum(items)"
    user = manager.get_user_prompt("fix_typos", code)
    print(f"✓ User prompt: {user[:50]}...\n")
    
    # Test 3: Get full prompt (ready for API)
    print("Test 3: Getting full prompt for API call")
    full = manager.get_full_prompt("fix_typos", code)
    print(f"✓ System: {full['system'][:40]}...")
    print(f"✓ User: {full['user'][:40]}...\n")
    
    # Test 4: Dynamic variables
    print("Test 4: Template with variables")
    text = "Hello world"
    prompt = manager.get_user_prompt("translate", text, target_language="Spanish")
    print(f"✓ Prompt: {prompt}\n")
    
    # Test 5: List all actions
    print("Test 5: Listing all actions")
    actions = manager.list_actions()
    print(f"✓ Total actions: {len(actions)}")
    print(f"✓ Sample actions: {actions[:5]}\n")
    
    print("✅ All tests passed!")


def example_api_ready():
    """Show how this integrates with actual API calls."""
    print("🔌 Example: Preparing for OpenAI API call\n")
    
    manager = PromptManager()
    
    # Simulate clipboard content
    code = """def calcluate_total(items):
    sum = 0
    for item in itmes:
        sum += item.price
    return sum"""
    
    # User clicks "Fix Typos" button
    action = "fix_typos"
    
    # Get prompts
    prompts = manager.get_full_prompt(action, code)
    
    # This is what you'd send to OpenAI/Groq:
    print("Ready to send to API:")
    print(f"""
messages = [
    {{
        "role": "system",
        "content": "{prompts['system'][:60]}..."
    }},
    {{
        "role": "user", 
        "content": "{prompts['user'][:60]}..."
    }}
]
    """)
    
    print("\n🚀 Next step: Actually call the API!")


if __name__ == "__main__":
    # Run tests
    test_prompt_manager()
    
    print("\n" + "="*60 + "\n")
    
    # Show API integration example
    example_api_ready()