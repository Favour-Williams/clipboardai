"""
Database Module for ClipboardAI

Handles SQLite storage for action history and statistics.

LEARNING FOCUS: SQLite, database design, SQL queries
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional


class Database:
    """
    Manages SQLite database for ClipboardAI history.
    
    Schema:
    - history: stores all AI actions and results
    - settings: stores user preferences (future)
    """
    
    def __init__(self, db_path: str = 'clipboardai.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
    
    def get_connection(self):
        """Get or create database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        return self.conn
    
    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                model TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                input_length INTEGER,
                output_length INTEGER
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action 
            ON history(action)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON history(timestamp DESC)
        ''')
        
        # Create settings table (for future use)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Database initialized")
    
    def add_history(
        self,
        action: str,
        input_text: str,
        output_text: str,
        tokens_used: int = 0,
        model: str = None
    ) -> int:
        """
        Add an action to history.
        
        Args:
            action: Action name (e.g., "fix_typos")
            input_text: Original clipboard content
            output_text: AI-generated result
            tokens_used: Number of tokens consumed
            model: AI model used
            
        Returns:
            ID of inserted record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO history (
                action, input_text, output_text, tokens_used, model,
                input_length, output_length
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            action,
            input_text,
            output_text,
            tokens_used,
            model,
            len(input_text),
            len(output_text)
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_history(
        self,
        limit: int = 50,
        action_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent history items.
        
        Args:
            limit: Maximum number of items to return
            action_filter: Filter by action name (optional)
            
        Returns:
            List of history items with previews
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                id,
                action,
                substr(input_text, 1, 100) as input_preview,
                substr(output_text, 1, 100) as output_preview,
                tokens_used,
                model,
                timestamp,
                input_length,
                output_length
            FROM history
        '''
        
        params = []
        if action_filter:
            query += ' WHERE action = ?'
            params.append(action_filter)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_history_item(self, history_id: int) -> Optional[Dict]:
        """
        Get full details of a history item.
        
        Args:
            history_id: ID of history item
            
        Returns:
            Full history item or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM history WHERE id = ?
        ''', (history_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_history_item(self, history_id: int) -> bool:
        """
        Delete a history item.
        
        Args:
            history_id: ID of item to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM history WHERE id = ?', (history_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def clear_history(self):
        """Clear all history."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM history')
        conn.commit()
        
        print(f"🗑️  Cleared {cursor.rowcount} history items")
    
    def get_stats(self) -> Dict:
        """
        Get usage statistics.
        
        Returns:
            dict with various statistics
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) as count FROM history')
        total_count = cursor.fetchone()['count']
        
        # Total tokens
        cursor.execute('SELECT SUM(tokens_used) as total FROM history')
        total_tokens = cursor.fetchone()['total'] or 0
        
        # Actions breakdown
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM history
            GROUP BY action
            ORDER BY count DESC
        ''')
        actions_by_type = {
            row['action']: row['count']
            for row in cursor.fetchall()
        }
        
        # Average tokens per action
        cursor.execute('''
            SELECT AVG(tokens_used) as avg_tokens
            FROM history
        ''')
        avg_tokens = cursor.fetchone()['avg_tokens'] or 0
        
        return {
            'total_count': total_count,
            'total_tokens': total_tokens,
            'actions_by_type': actions_by_type,
            'avg_tokens_per_action': round(avg_tokens, 2)
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# ==============================================================================
# TESTING
# ==============================================================================

def test_database():
    """Test database functionality."""
    print("🧪 Testing Database\n")
    
    # Use test database
    db = Database('test_clipboardai.db')
    db.init_db()
    
    # Add some test data
    print("Adding test history...")
    id1 = db.add_history(
        action="fix_typos",
        input_text="def calcluate(): pass",
        output_text="def calculate(): pass",
        tokens_used=150,
        model="gpt-4o-mini"
    )
    print(f"✓ Added history item {id1}")
    
    id2 = db.add_history(
        action="translate",
        input_text="Hello world",
        output_text="Hola mundo",
        tokens_used=50,
        model="gpt-4o-mini"
    )
    print(f"✓ Added history item {id2}")
    
    # Get history
    print("\nFetching history...")
    history = db.get_history(limit=10)
    print(f"✓ Found {len(history)} items")
    for item in history:
        print(f"   {item['id']}: {item['action']} ({item['tokens_used']} tokens)")
    
    # Get specific item
    print(f"\nFetching item {id1}...")
    item = db.get_history_item(id1)
    print(f"✓ Input: {item['input_text']}")
    print(f"✓ Output: {item['output_text']}")
    
    # Get stats
    print("\nGetting stats...")
    stats = db.get_stats()
    print(f"✓ Total actions: {stats['total_count']}")
    print(f"✓ Total tokens: {stats['total_tokens']}")
    print(f"✓ Actions by type: {stats['actions_by_type']}")
    
    # Clean up
    print("\nCleaning up...")
    db.clear_history()
    db.close()
    
    import os
    os.remove('test_clipboardai.db')
    print("✓ Test database removed")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_database()