import sqlite3

conn = sqlite3.connect("survey.db")
c = conn.cursor()

c.execute(
    """
CREATE TABLE IF NOT EXISTS survey_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_sid TEXT,
    phone TEXT,
    question TEXT,
    answer TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
)

c.execute(
    """
CREATE TABLE IF NOT EXISTS call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_sid TEXT,
    phone TEXT,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
)

c.execute(
    """
CREATE TABLE IF NOT EXISTS survey_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    expected_input TEXT DEFAULT "dtmf",
    is_active INTEGER DEFAULT 1
);
"""
)


conn.commit()
conn.close()

print("Database initialized")
