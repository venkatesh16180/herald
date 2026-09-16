import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS briefings (
        id INTEGER PRIMARY KEY, generated_at TEXT, script TEXT,
        audio_path TEXT, word_count INTEGER)''')
    conn.commit()
    conn.close()

def log_briefing(script, audio_path, word_count, generated_at):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO briefings (generated_at, script, audio_path, word_count) VALUES (?,?,?,?)',
                 (generated_at.isoformat(), script, audio_path, word_count))
    conn.commit()
    conn.close()