import sqlite3
import os
from flask_login import UserMixin

DB_NAME = "users.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_NAME):
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        ''')
        conn.execute('''
            CREATE TABLE threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                thread_id TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        print("Initialized users.db")
    
    # Ensure default admin exists
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM users WHERE role = 'admin'").fetchone()
    if not admin:
        from werkzeug.security import generate_password_hash
        # Default Admin: admin@college.edu / admin123
        pw_hash = generate_password_hash("admin123", method='scrypt')
        conn.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                     ("admin@college.edu", pw_hash, "admin"))
        conn.commit()
        print("Created default admin: admin@college.edu / admin123")
    conn.close()

class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role

def get_user_by_id(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['email'], user_data['role'])
    return None

def get_user_by_email(email):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user_data

def create_user(email, password_hash, role='student'):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                     (email, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Thread Helpers
def create_thread_entry(user_id, thread_id, name="New Chat"):
    conn = get_db_connection()
    conn.execute('INSERT INTO threads (user_id, thread_id, name) VALUES (?, ?, ?)',
                 (user_id, thread_id, name))
    conn.commit()
    conn.close()

def get_user_threads(user_id):
    conn = get_db_connection()
    threads = conn.execute('SELECT * FROM threads WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    conn.close()
    return threads

def get_thread_owner(thread_id):
    conn = get_db_connection()
    row = conn.execute('SELECT user_id FROM threads WHERE thread_id = ?', (thread_id,)).fetchone()
    conn.close()
    return row['user_id'] if row else None

def update_thread_name(thread_id, name):
    conn = get_db_connection()
    conn.execute('UPDATE threads SET name = ? WHERE thread_id = ?', (name, thread_id))
    conn.commit()
    conn.close()
