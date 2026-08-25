import sqlite3
from pathlib import Path
from datetime import datetime

class AnalyticsLogger:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    query TEXT,
                    has_llm_answer BOOLEAN,
                    source_count INTEGER
                )
            ''')
            conn.commit()

    def log_query(self, query: str, has_llm: bool, source_count: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO queries (timestamp, query, has_llm_answer, source_count) VALUES (?, ?, ?, ?)',
                (datetime.now().isoformat(), query, has_llm, source_count)
            )
            conn.commit()

    def get_recent_queries(self, limit: int = 5):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT timestamp, query FROM queries ORDER BY id DESC LIMIT ?', (limit,))
            return cursor.fetchall()
            
    def get_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*), SUM(has_llm_answer) FROM queries')
            row = cursor.fetchone()
            total = row[0] or 0
            llm_count = row[1] or 0
            return {"total_queries": total, "llm_answered": llm_count}
