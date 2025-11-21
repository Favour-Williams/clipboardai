"""
ClipboardAI Flask Application

This is the web API that exposes ClipboardAI functionality.

LEARNING FOCUS: REST API design, Flask routing, CORS handling
"""
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from datetime import datetime

# Import our custom modules
from prompt_manager import PromptManager
from ai_processor import AIProcessor, AIConfig, ClipboardAIEngine
from context_detector import ContextDetector
from database import Database

if os.getenv('DATABASE_URL'):
    from database_postgres import Database
    print("🐘 Using PostgreSQL (Production)")
else:
    from database import Database
    print("🗄️  Using SQLite (Development)")
# ==============================================================================
# APP INITIALIZATION
# ==============================================================================

app = Flask(__name__)
CORS(app)  # Allow frontend to call API

# Initialize components
prompt_manager = PromptManager()
context_detector = ContextDetector()
if os.getenv('DATABASE_URL'):
    database = Database()  # PostgreSQL gets URL from environment
else:
    database = Database('clipboardai.db')
database.init_db()

# Initialize AI processor
ai_config = AIConfig(
    provider=os.getenv("AI_PROVIDER", "openai"),  # openai or groq
    model=os.getenv("AI_MODEL", "gpt-4o-mini"),
    temperature=float(os.getenv("AI_TEMPERATURE", "0.3"))
)

try:
    ai_processor = AIProcessor(ai_config)
    engine = ClipboardAIEngine(prompt_manager, ai_processor)
    print("✅ ClipboardAI Engine initialized")
except ValueError as e:
    print(f"⚠️  Warning: AI processor not initialized - {e}")
    engine = None


# ==============================================================================
# API ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Serve the main UI."""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'ai_enabled': engine is not None,
        'provider': ai_config.provider if engine else None,
        'model': ai_config.model if engine else None
    })


@app.route('/api/detect', methods=['POST'])
def detect_content():
    """
    Detect content type from clipboard text.
    
    Request body:
    {
        "content": "text to analyze"
    }
    
    Response:
    {
        "type": "python_code",
        "confidence": 0.85,
        "suggested_actions": ["fix_typos", "add_docstring"],
        "metadata": {...}
    }
    """
    data = request.json
    content = data.get('content', '')
    
    if not content:
        return jsonify({'error': 'No content provided'}), 400
    
    result = context_detector.detect(content)
    
    return jsonify({
        'type': result['type'].value,
        'confidence': result['confidence'],
        'suggested_actions': result['suggested_actions'],
        'metadata': result['metadata']
    })


@app.route('/api/process', methods=['POST'])
def process_action():
    """
    Process clipboard content with an AI action.
    
    Request body:
    {
        "action": "fix_typos",
        "content": "def calcluate(): pass",
        "params": {  // optional
            "target_language": "Spanish"
        }
    }
    
    Response:
    {
        "success": true,
        "result": "def calculate(): pass",
        "tokens_used": 150,
        "action": "fix_typos",
        "history_id": 123
    }
    """
    if not engine:
        return jsonify({
            'error': 'AI engine not initialized. Check API key configuration.'
        }), 503
    
    data = request.json
    action = data.get('action')
    content = data.get('content')
    params = data.get('params', {})
    
    # Validate input
    if not action or not content:
        return jsonify({'error': 'Missing action or content'}), 400
    
    # Execute action
    result = engine.execute_action(action, content, **params)
    
    # Save to history if successful
    history_id = None
    if result['success']:
        history_id = database.add_history(
            action=action,
            input_text=content,
            output_text=result['content'],
            tokens_used=result['tokens_used'],
            model=result['model']
        )
    
    # Build response
    response = {
        'success': result['success'],
        'result': result['content'],
        'tokens_used': result.get('tokens_used', 0),
        'action': action,
        'history_id': history_id
    }
    
    if not result['success']:
        response['error'] = result.get('error', 'Unknown error')
    
    return jsonify(response)


@app.route('/api/actions', methods=['GET'])
def list_actions():
    """
    List all available actions.
    
    Response:
    {
        "actions": [
            {
                "name": "fix_typos",
                "description": "Fix spelling and syntax errors",
                "category": "code"
            },
            ...
        ]
    }
    """
    actions = [
        # Code actions
        {"name": "fix_typos", "description": "Fix spelling and syntax errors", "category": "code"},
        {"name": "add_docstring", "description": "Add Python docstring", "category": "code"},
        {"name": "generate_tests", "description": "Generate unit tests", "category": "code"},
        {"name": "explain_code", "description": "Explain what code does", "category": "code"},
        
        # Git actions
        {"name": "generate_commit", "description": "Generate commit message", "category": "git"},
        {"name": "summarize_changes", "description": "Summarize code changes", "category": "git"},
        
        # Text actions
        {"name": "fix_grammar", "description": "Fix grammar and spelling", "category": "text"},
        {"name": "translate", "description": "Translate to another language", "category": "text"},
        {"name": "summarize", "description": "Summarize text", "category": "text"},
        {"name": "extract_keywords", "description": "Extract keywords", "category": "text"},
        
        # Data actions
        {"name": "format_json", "description": "Format JSON", "category": "data"},
        {"name": "format_sql", "description": "Format SQL", "category": "data"},
    ]
    
    return jsonify({"actions": actions})


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get action history.
    
    Query params:
    - limit: number of results (default: 50)
    - action: filter by action name
    
    Response:
    {
        "history": [
            {
                "id": 1,
                "action": "fix_typos",
                "input_preview": "def calcluate()...",
                "output_preview": "def calculate()...",
                "tokens_used": 150,
                "timestamp": "2025-01-15T10:30:00"
            },
            ...
        ]
    }
    """
    limit = request.args.get('limit', 50, type=int)
    action = request.args.get('action')
    
    history = database.get_history(limit=limit, action_filter=action)
    
    return jsonify({"history": history})


@app.route('/api/history/<int:history_id>', methods=['GET'])
def get_history_item(history_id):
    """
    Get full details of a history item.
    
    Response:
    {
        "id": 1,
        "action": "fix_typos",
        "input_text": "full input...",
        "output_text": "full output...",
        "tokens_used": 150,
        "model": "gpt-4o-mini",
        "timestamp": "2025-01-15T10:30:00"
    }
    """
    item = database.get_history_item(history_id)
    
    if not item:
        return jsonify({'error': 'History item not found'}), 404
    
    return jsonify(item)


@app.route('/api/history/<int:history_id>', methods=['DELETE'])
def delete_history_item(history_id):
    """Delete a history item."""
    success = database.delete_history_item(history_id)
    
    if not success:
        return jsonify({'error': 'History item not found'}), 404
    
    return jsonify({'success': True})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get usage statistics.
    
    Response:
    {
        "total_requests": 150,
        "total_tokens": 45000,
        "estimated_cost": 0.0168,
        "actions_by_type": {
            "fix_typos": 50,
            "translate": 30,
            ...
        },
        "history_count": 150
    }
    """
    if not engine:
        return jsonify({'error': 'AI engine not initialized'}), 503
    
    # Get AI stats
    ai_stats = engine.get_stats()
    
    # Get database stats
    db_stats = database.get_stats()
    
    return jsonify({
        'total_requests': ai_stats['ai_stats']['total_requests'],
        'total_tokens': ai_stats['ai_stats']['total_tokens'],
        'estimated_cost': ai_stats['estimated_cost'],
        'actions_by_type': db_stats['actions_by_type'],
        'history_count': db_stats['total_count']
    })


@app.route('/api/prompts/<action>', methods=['GET'])
def get_prompt(action):
    """
    Get the system prompt for an action (for transparency/customization).
    
    Response:
    {
        "action": "fix_typos",
        "system_prompt": "You are a strict code typo fixer..."
    }
    """
    try:
        system_prompt = prompt_manager.get_system_prompt(action)
        return jsonify({
            'action': action,
            'system_prompt': system_prompt
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/prompts/<action>', methods=['PUT'])
def update_prompt(action):
    """
    Update the system prompt for an action (advanced users).
    
    Request body:
    {
        "system_prompt": "new prompt..."
    }
    """
    data = request.json
    new_prompt = data.get('system_prompt')
    
    if not new_prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        prompt_manager.save_custom_prompt(action, new_prompt)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


# ==============================================================================
# RUN APP
# ==============================================================================

if __name__ == '__main__':
    # Initialize database
    database.init_db()
    
    # Run app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"\n{'='*60}")
    print("🚀 ClipboardAI Server Starting")
    print(f"{'='*60}")
    print(f"   URL: http://localhost:{port}")
    print(f"   AI Provider: {ai_config.provider}")
    print(f"   Model: {ai_config.model}")
    print(f"   Debug Mode: {debug}")
    print(f"{'='*60}\n")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )


