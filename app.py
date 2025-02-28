#<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 20:04:21 2025

@author: Rebekah
"""

import os
import sqlite3
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

FLOW_URL = (
    "https://prod-35.westus.logic.azure.com:443/workflows/37c3bf8a61df45c4b2e4de82e1e932c5/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=mjOa4NAb6ZnH_D1dvtDE3-Xb7MdPfkp0wgO926jdh3I"
)

# Name of the local SQLite database file
DB_FILE = "submissions.db"


def init_db():
    """Create or recreate the submissions table with all needed columns."""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Create the table with columns matching our new form fields
        c.execute('''
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_first_name TEXT NOT NULL,
                volunteer_last_name TEXT NOT NULL,
                volunteer_email TEXT NOT NULL,
                program_name TEXT NOT NULL,
                event_activity_name TEXT NOT NULL,
                date_volunteered TEXT NOT NULL,
                volunteer_hours REAL NOT NULL,
                comments_feedback TEXT,
                shoutouts_highlights TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()


# Call init_db() so it's always invoked
init_db()


@app.route('/')
def home():
    """
    Render the home.html form.
    Ensure home.html has the matching `name="..."` attributes in the <form>.
    """
    return render_template('home.html')


@app.route('/submit', methods=['POST'])
def submit_data():
    """
    Handle form submissions and insert into SQLite,
    then send to Power Automate for SharePoint.
    """
    # 1) Get the data from the form (matching the `name` attributes in your HTML)
    volunteer_first_name   = request.form.get('volunteer_first_name')
    volunteer_last_name    = request.form.get('volunteer_last_name')
    volunteer_email        = request.form.get('volunteer_email')
    program_name           = request.form.get('program_name')
    event_activity_name    = request.form.get('event_activity_name')
    date_volunteered       = request.form.get('date_volunteered')
    volunteer_hours        = request.form.get('volunteer_hours')
    comments_feedback      = request.form.get('comments_feedback')
    shoutouts_highlights   = request.form.get('shoutouts_highlights')

    # 2) Basic validation 
    if not volunteer_first_name or not volunteer_last_name or not volunteer_email:
        return "Volunteer first name, last name, and email are required fields!", 400

    if not program_name or not event_activity_name or not date_volunteered or not volunteer_hours:
        return "Please fill in the required program/activity/date/hours fields.", 400

    # 3) Insert into local SQLite DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO submissions (
            volunteer_first_name,
            volunteer_last_name,
            volunteer_email,
            program_name,
            event_activity_name,
            date_volunteered,
            volunteer_hours,
            comments_feedback,
            shoutouts_highlights
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) 
    ''', (
        volunteer_first_name,
        volunteer_last_name,
        volunteer_email,
        program_name,
        event_activity_name,
        date_volunteered,
        volunteer_hours,
        comments_feedback,
        shoutouts_highlights
    ))
    conn.commit()
    conn.close()

    # 4) Send the same data to Power Automate (Flow) for SharePoint blahfv
    payload = {
        "volunteer_first_name":  volunteer_first_name,
        "volunteer_last_name":   volunteer_last_name,
        "volunteer_email":       volunteer_email,
        "program_name":          program_name,
        "event_activity_name":   event_activity_name,
        "date_volunteered":      date_volunteered,
        "volunteer_hours":       volunteer_hours,
        "comments_feedback":     comments_feedback,
        "shoutouts_highlights":  shoutouts_highlights
    }
    try:
        response = requests.post(FLOW_URL, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error posting to Power Automate:", e)
        return (
            "Your submission was saved locally, but we couldn't send it to SharePoint.",
            500
        )

    # 5) Return a success message
    return "Thanks! Your submission was recorded locally and sent to SharePoint via Power Automate."


if __name__ == '__main__':
    # For local development/debug
    app.run(debug=True)
#=======
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 20:04:21 2025

@author: Rebekah
"""

import os
import sqlite3
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

FLOW_URL = (
    "https://prod-35.westus.logic.azure.com:443/workflows/37c3bf8a61df45c4b2e4de82e1e932c5/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=mjOa4NAb6ZnH_D1dvtDE3-Xb7MdPfkp0wgO926jdh3I"
)

# Name of the local SQLite database file
DB_FILE = "submissions.db"


def init_db():
    """Create or recreate the submissions table with all needed columns."""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Create the table with columns matching our new form fields
        c.execute('''
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_first_name TEXT NOT NULL,
                volunteer_last_name TEXT NOT NULL,
                volunteer_email TEXT NOT NULL,
                program_name TEXT NOT NULL,
                event_activity_name TEXT NOT NULL,
                date_volunteered TEXT NOT NULL,
                volunteer_hours REAL NOT NULL,
                comments_feedback TEXT,
                shoutouts_highlights TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()


# Call init_db() so it's always invoked
init_db()


@app.route('/')
def home():
    """
    Render the home.html form.
    Ensure home.html has the matching `name="..."` attributes in the <form>.
    """
    return render_template('home.html')


@app.route('/submit', methods=['POST'])
def submit_data():
    """
    Handle form submissions and insert into SQLite,
    then send to Power Automate for SharePoint.
    """
    # 1) Get the data from the form (matching the `name` attributes in your HTML)
    volunteer_first_name   = request.form.get('volunteer_first_name')
    volunteer_last_name    = request.form.get('volunteer_last_name')
    volunteer_email        = request.form.get('volunteer_email')
    program_name           = request.form.get('program_name')
    event_activity_name    = request.form.get('event_activity_name')
    date_volunteered       = request.form.get('date_volunteered')
    volunteer_hours        = request.form.get('volunteer_hours')
    comments_feedback      = request.form.get('comments_feedback')
    shoutouts_highlights   = request.form.get('shoutouts_highlights')

    # 2) Basic validation 
    if not volunteer_first_name or not volunteer_last_name or not volunteer_email:
        return "Volunteer first name, last name, and email are required fields!", 400

    if not program_name or not event_activity_name or not date_volunteered or not volunteer_hours:
        return "Please fill in the required program/activity/date/hours fields.", 400

    # 3) Insert into local SQLite DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO submissions (
            volunteer_first_name,
            volunteer_last_name,
            volunteer_email,
            program_name,
            event_activity_name,
            date_volunteered,
            volunteer_hours,
            comments_feedback,
            shoutouts_highlights
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        volunteer_first_name,
        volunteer_last_name,
        volunteer_email,
        program_name,
        event_activity_name,
        date_volunteered,
        volunteer_hours,
        comments_feedback,
        shoutouts_highlights
    ))
    conn.commit()
    conn.close()

    # 4) Send the same data to Power Automate (Flow) for SharePoint blahfv
    payload = {
        "volunteer_first_name":  volunteer_first_name,
        "volunteer_last_name":   volunteer_last_name,
        "volunteer_email":       volunteer_email,
        "program_name":          program_name,
        "event_activity_name":   event_activity_name,
        "date_volunteered":      date_volunteered,
        "volunteer_hours":       volunteer_hours,
        "comments_feedback":     comments_feedback,
        "shoutouts_highlights":  shoutouts_highlights
    }
    try:
        response = requests.post(FLOW_URL, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error posting to Power Automate:", e)
        return (
            "Your submission was saved locally, but we couldn't send it to SharePoint.",
            500
        )

    # 5) Return a success message
    return "Thanks! Your submission was recorded locally and sent to SharePoint via Power Automate."


if __name__ == '__main__':
    # For local development/debug
    app.run(debug=True)
#>>>>>>> c5f020e7619d728379c9bdf7c8d60eb32ae0b064
