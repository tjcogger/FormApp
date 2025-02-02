# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 20:04:21 2025

@author: Rebekah
"""

import os
import sqlite3
import requests  # <-- ADDED for HTTP POST
from flask import Flask, render_template, request
 
app = Flask(__name__)

FLOW_URL = "https://prod-35.westus.logic.azure.com:443/workflows/37c3bf8a61df45c4b2e4de82e1e932c5/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=mjOa4NAb6ZnH_D1dvtDE3-Xb7MdPfkp0wgO926jdh3I"

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
    """Handle form submissions and insert into SQLite database, then send to Power Automate."""
    # 1) Get the data from the form
    name = request.form.get('name')
    email = request.form.get('email')
    comments = request.form.get('comments')

    # 2) Basic validation
    if not name or not email:
        return "Name and Email are required fields!", 400

    # 3) Insert into DB (local SQLite)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO submissions (name, email, comments)
        VALUES (?, ?, ?)
    ''', (name, email, comments))
    conn.commit()
    conn.close()

    # 4) Send the same data to Power Automate (Flow) for SharePoint
    payload = {
        "name": name,
        "email": email,
        "comments": comments
    }
    try:
        response = requests.post(FLOW_URL, json=payload)
        response.raise_for_status()  # Raise an error if the request failed
    except requests.exceptions.RequestException as e:
        print("Error posting to Power Automate:", e)
        return "Your submission was saved locally, but failed to send to SharePoint.", 500

    # 5) Return a success message
    return "Thanks! Your submission was recorded locally and sent to SharePoint via Power Automate."

if __name__ == '__main__':
    # For local development/debug
    app.run(debug=True)
