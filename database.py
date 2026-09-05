import sqlite3
import datetime
import os
import shutil
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_path():
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_db = "/tmp/quiz_bot.db"
        orig_db = os.path.join(BASE_DIR, "quiz_bot.db")
        if not os.path.exists(tmp_db) and os.path.exists(orig_db):
            try:
                shutil.copyfile(orig_db, tmp_db)
            except Exception:
                pass
        return tmp_db
    return os.path.join(BASE_DIR, "quiz_bot.db")

def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        username TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tests_count INTEGER DEFAULT 0,
        total_score INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 0
    )
    """)
    
    # Quiz results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        total_q INTEGER,
        correct_q INTEGER,
        percentage REAL,
        duration_sec INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)
    
    # User mistakes table for retry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        collection_id INTEGER,
        question_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, collection_id, question_id)
    )
    """)
    
    # Active user quiz sessions table for serverless persistence
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_sessions (
        user_id INTEGER PRIMARY KEY,
        session_data TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def save_user_session(user_id: int, session_data: dict):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO active_sessions (user_id, session_data, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id) DO UPDATE SET
        session_data = excluded.session_data,
        updated_at = CURRENT_TIMESTAMP
    """, (user_id, json.dumps(session_data, ensure_ascii=False)))
    conn.commit()
    conn.close()

def get_user_session(user_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT session_data FROM active_sessions WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return None
    return None

def delete_user_session(user_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

class PersistentSessions:
    def __init__(self):
        self._cache = {}

    def get(self, user_id: int, default=None):
        if user_id in self._cache:
            return self._cache[user_id]
        data = get_user_session(user_id)
        if data is not None:
            self._cache[user_id] = data
            return data
        return default

    def __getitem__(self, user_id: int):
        val = self.get(user_id)
        if val is None:
            raise KeyError(user_id)
        return val

    def __setitem__(self, user_id: int, data: dict):
        self._cache[user_id] = data
        save_user_session(user_id, data)

    def __delitem__(self, user_id: int):
        self._cache.pop(user_id, None)
        delete_user_session(user_id)

    def __contains__(self, user_id: int):
        return self.get(user_id) is not None

    def sync(self, user_id: int):
        if user_id in self._cache:
            save_user_session(user_id, self._cache[user_id])

sessions = PersistentSessions()

def register_user(user_id: int, full_name: str, username: str = None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (user_id, full_name, username)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        full_name = excluded.full_name,
        username = excluded.username
    """, (user_id, full_name, username))
    conn.commit()
    conn.close()

def save_quiz_result(user_id: int, category: str, total_q: int, correct_q: int, duration_sec: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    percentage = round((correct_q / total_q) * 100, 1) if total_q > 0 else 0
    
    cursor.execute("""
    INSERT INTO quiz_results (user_id, category, total_q, correct_q, percentage, duration_sec)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, category, total_q, correct_q, percentage, duration_sec))
    
    cursor.execute("""
    UPDATE users SET
        tests_count = tests_count + 1,
        total_score = total_score + ?,
        total_questions = total_questions + ?
    WHERE user_id = ?
    """, (correct_q, total_q, user_id))
    
    conn.commit()
    conn.close()

def save_user_mistake(user_id: int, collection_id: int, question_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO user_mistakes (user_id, collection_id, question_id)
    VALUES (?, ?, ?)
    """, (user_id, collection_id, question_id))
    conn.commit()
    conn.close()

def remove_user_mistake(user_id: int, collection_id: int, question_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
    DELETE FROM user_mistakes
    WHERE user_id = ? AND collection_id = ? AND question_id = ?
    """, (user_id, collection_id, question_id))
    conn.commit()
    conn.close()

def get_user_mistakes(user_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
    SELECT collection_id, question_id FROM user_mistakes WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user_stats(user_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
    SELECT full_name, tests_count, total_score, total_questions
    FROM users WHERE user_id = ?
    """, (user_id,))
    user = cursor.fetchone()
    
    cursor.execute("""
    SELECT COUNT(*) FROM user_mistakes WHERE user_id = ?
    """, (user_id,))
    mistakes_count = cursor.fetchone()[0]
    
    conn.close()
    if user:
        return {
            "name": user[0],
            "tests_count": user[1],
            "total_score": user[2],
            "total_questions": user[3],
            "mistakes_count": mistakes_count,
            "accuracy": round((user[2] / user[3]) * 100, 1) if user[3] > 0 else 0
        }
    return None

def get_leaderboard(limit: int = 10):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
    SELECT full_name, total_score, total_questions, tests_count
    FROM users
    WHERE tests_count > 0
    ORDER BY total_score DESC, (CAST(total_score AS REAL) / total_questions) DESC
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows
