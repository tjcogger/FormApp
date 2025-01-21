# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 20:04:21 2025

@author: Thomas
"""

import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# Name of the local SQLite database file
DB_FILE = "submissions.db"

def init_db():
    """Create the submissions table if it doesn't exist yet."""
    # Only create the file + table if DB_FILE doesn't exist
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

# Call init_db() here so it's always invoked, even under gunicorn
init_db()

@app.route('/')
def home():
    """Render the home.html form."""
    return render_template('home.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    """Handle form submissions and insert into SQLite database."""
    # 1) Get the data from the form
    name = request.form.get('name')
    email = request.form.get('email')
    comments = request.form.get('comments')

    # 2) Basic validation
    if not name or not email:
        return "Name and Email are required fields!", 400

    # 3) Insert into DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO submissions (name, email, comments)
        VALUES (?, ?, ?)
    ''', (name, email, comments))
    conn.commit()
    conn.close()

    # 4) Return a success message (or redirect to a "thank you" page)
    return "Thanks! Your submission has been recorded."

if __name__ == '__main__':
    # For local development/debug
    app.run(debug=True)
