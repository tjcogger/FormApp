# -*- coding: utf-8 -*-
"""
Volunteer submission form → SQLite backup → SharePoint via Power Automate
Identical to the original script except FLOW_URL now targets the second flow.
"""

import os
import sqlite3
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# ----------------------------------------------------------------------
# Power Automate webhook URL (SECOND flow)
# ----------------------------------------------------------------------
FLOW_URL = (
    "https://prod-143.westus.logic.azure.com:443/workflows/7a0e4f601d6e4dfaa1423b3d921746ef/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=nZJo1sU2uucPTPgQdCiICxOcbDdQyzMO2LG9N22feqY"
)

# ----------------------------------------------------------------------
# Local SQLite settings
# ----------------------------------------------------------------------
DB_FILE = "submissions.db"


def init_db() -> None:
    """Create the submissions table once if the DB is missing."""
    if os.path.exists(DB_FILE):
        return

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volunteer_first_name TEXT NOT NULL,
                volunteer_last_name  TEXT NOT NULL,
                volunteer_email      TEXT NOT NULL,
                program_name         TEXT NOT NULL,
                event_activity_name  TEXT NOT NULL,
                date_volunteered     TEXT NOT NULL,
                volunteer_hours      REAL NOT NULL,
                comments_feedback    TEXT,
                shoutouts_highlights TEXT,
                created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# Ensure DB exists at startup
init_db()

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route("/")
def home():
    """Serve the HTML form."""
    return render_template("home.html")


@app.route("/submit", methods=["POST"])
def submit_data():
    """Validate form, persist locally, then forward to Power Automate."""
    volunteer_first_name = request.form.get("volunteer_first_name", "").strip()
    volunteer_last_name  = request.form.get("volunteer_last_name", "").strip()
    volunteer_email      = request.form.get("volunteer_email", "").strip()
    program_name         = request.form.get("program_name", "").strip()
    event_activity_name  = request.form.get("event_activity_name", "").strip()
    date_volunteered     = request.form.get("date_volunteered", "").strip()
    volunteer_hours      = request.form.get("volunteer_hours", "").strip()
    comments_feedback    = request.form.get("comments_feedback", "").strip()
    shoutouts_highlights = request.form.get("shoutouts_highlights", "").strip()

    # Basic validation
    required = [
        volunteer_first_name, volunteer_last_name, volunteer_email,
        program_name, event_activity_name, date_volunteered, volunteer_hours,
    ]
    if not all(required):
        return "Missing required fields.", 400

    # Save to SQLite
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            INSERT INTO submissions (
                volunteer_first_name, volunteer_last_name, volunteer_email,
                program_name, event_activity_name, date_volunteered,
                volunteer_hours, comments_feedback, shoutouts_highlights
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                volunteer_first_name, volunteer_last_name, volunteer_email,
                program_name, event_activity_name, date_volunteered,
                volunteer_hours, comments_feedback, shoutouts_highlights,
            ),
        )

    # Forward to Power Automate
    payload = {
        "volunteer_first_name": volunteer_first_name,
        "volunteer_last_name":  volunteer_last_name,
        "volunteer_email":      volunteer_email,
        "program_name":         program_name,
        "event_activity_name":  event_activity_name,
        "date_volunteered":     date_volunteered,
        "volunteer_hours":      volunteer_hours,
        "comments_feedback":    comments_feedback,
        "shoutouts_highlights": shoutouts_highlights,
    }

    try:
        response = requests.post(FLOW_URL, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print("Error posting to Power Automate:", exc)
        return (
            "Saved locally, but we couldn’t send it to SharePoint. "
            "Please notify IT.",
            502,
        )

    return "Thank you! Your submission was recorded and sent to SharePoint."


# ----------------------------------------------------------------------
if __name__ == "__main__":
    # For local testing only; behind nginx/Gunicorn in production
    app.run(debug=True)
