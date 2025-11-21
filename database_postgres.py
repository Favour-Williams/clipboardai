"""
PostgreSQL Database Module for ClipboardAI (Production)

This replaces database.py for cloud deployment with PostgreSQL.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional


class Database:
    """
    Manages PostgreSQL database for ClipboardAI history.
    
    Works with Render's PostgreSQL addon.
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize database connection.
        
        Args:
            db_url: PostgreSQL connection URL (from DATABASE_URL env var)
        """
        self.db_url = db_url or os.getenv('DATABASE_URL')
        
        if not self.db_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Make sure PostgreSQL is configured on Render."
            )
        
        # Fix for psycopg2: Render uses 'postgres://' but psycopg2 needs 'postgresql://'
        if self.db_url.startswith('postgres://'):
            self.db_url = self.db_url.replace('postgres://', 'postgresql://', 1)
        
        self.conn = None
    
    def get_connection(self):
        """Get or create database connection."""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(
                self.db_url,
                cursor_factory=RealDictCursor
            )
        return self.conn
    
    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                action TEXT NOT NULL,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                model TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                input_length INTEGER,
                output_length INTEGER
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action 
            ON history(action)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON history(timestamp DESC)
        ''')
        
        # Create settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ PostgreSQL database initialized")
    
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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            action,
            input_text,
            output_text,
            tokens_used,
            model,
            len(input_text),
            len(output_text)
        ))
        
        record_id = cursor.fetchone()['id']
        conn.commit()
        return record_id
    
    def get_history(
        self,
        limit: int = 50,
        action_filter: Optional[str] = None
    ) -> List[Dict]:
        """Get recent history items."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                id,
                action,
                SUBSTRING(input_text, 1, 100) as input_preview,
                SUBSTRING(output_text, 1, 100) as output_preview,
                tokens_used,
                model,
                timestamp,
                input_length,
                output_length
            FROM history
        '''
        
        params = []
        if action_filter:
            query += ' WHERE action = %s'
            params.append(action_filter)
        
        query += ' ORDER BY timestamp DESC LIMIT %s'
        params.append(limit)
        
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_history_item(self, history_id: int) -> Optional[Dict]:
        """Get full details of a history item."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM history WHERE id = %s
        ''', (history_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_history_item(self, history_id: int) -> bool:
        """Delete a history item."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM history WHERE id = %s', (history_id,))
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
        """Get usage statistics."""
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
            'avg_tokens_per_action': round(float(avg_tokens), 2)
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Test function (only for local testing)
if __name__ == "__main__":
    print("⚠️  This is the PostgreSQL version.")
    print("   For local testing, use database.py (SQLite)")
    print("   For production on Render, this will be used automatically.")