import sqlite3

DB_NAME = 'meditime.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Users table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        userID TEXT PRIMARY KEY,
        Username TEXT UNIQUE NOT NULL,
        Password TEXT NOT NULL,
        Email TEXT,
        Role TEXT,
        reminderStatus BOOLEAN DEFAULT 1
    )
    ''')
    # Medications table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS medications (
        medicationID INTEGER PRIMARY KEY AUTOINCREMENT,
        userID TEXT,
        MedicationName TEXT NOT NULL,
        DosageAmount TEXT,
        Frequency TEXT,
        reminderTime TEXT,
        FOREIGN KEY(userID) REFERENCES users(userID)
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
