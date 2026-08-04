# -*- coding: utf-8 -*-
"""
Volunteer submission form → SQLite backup → SharePoint via Power Automate
Posts every submission to FLOW_URL_MAIN *and* to a program-specific flow
when the Program field matches. 
"""

import os
import sqlite3
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# ──────────────────────────────────────────────────────────────────────
# 1)  Power Automate web-hook URLs (env vars override literals)
# ──────────────────────────────────────────────────────────────────────
# -*- coding: utf-8 -*-

# ──────────────────────────────────────────────────────────────────────
# 1) Power Automate web-hook URLs (env vars override literals)
# ──────────────────────────────────────────────────────────────────────

FLOW_URL_MAIN = os.getenv(
    "FLOW_URL_MAIN",
    "https://prod-35.westus.logic.azure.com:443/workflows/37c3bf8a61df45c4b2e4de82e1e932c5/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=mjOa4NAb6ZnH_D1dvtDE3-Xb7MdPfkp0wgO926jdh3I",
)

PROGRAM_TO_URL = {
    "211": os.getenv(
        "FLOW_URL_211",
        "https://prod-143.westus.logic.azure.com:443/workflows/7a0e4f601d6e4dfaa1423b3d921746ef/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=nZJo1sU2uucPTPgQdCiICxOcbDdQyzMO2LG9N22feqY",
    ),
    "collective impact": os.getenv(
        "FLOW_URL_COLLECTIVE_IMPACT",
        "https://prod-88.westus.logic.azure.com:443/workflows/fc073cd921ed4a45a11df5a386f82cee/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=qlVPphes1g1gMwA7s-SGmtc_QuolucdgQG6a9tIQiaU",
    ),
    "learn with playgroup": os.getenv(
        "FLOW_URL_LEARN_WITH_PLAYGROUP",
        "https://prod-93.westus.logic.azure.com:443/workflows/a6aad79b686345a8b3f8bd8782b4f337/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Xj8gF0cQDCiWxncDOZJCY7zqhHRI4oVRVOvaETt0ePk",
    ),
    "little neighborhood libraries": os.getenv(
        "FLOW_URL_LITTLE_LIBRARIES",
        "https://prod-96.westus.logic.azure.com:443/workflows/d108c90980684890a6949af372f533cc/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=IOOdXQ07nIuE0hzEuk5t6f1x1O5pliWruNXLwGzoqW4",
    ),
    "nonprofit connection": os.getenv(
        "FLOW_URL_NONPROFIT_CONNECTION",
        "https://prod-117.westus.logic.azure.com:443/workflows/d91ecd30269b451dbdabc813155df949/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=_Vogaz2DaQ722a_MfnV6ZIhHkgJIw7IDIxkF7q26tXY",
    ),
    "student success program": os.getenv(
        "FLOW_URL_STUDENT_SUCCESS",
        "https://prod-58.westus.logic.azure.com:443/workflows/c77785cb0fa54209acfef52a8e2cfb27/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Gh9sp88xZWxrpe4qWBhyEIdckQqF34JTKliHiiyENQs",
    ),
    "weber ctc": os.getenv(
        "FLOW_URL_WEBER_CTC",
        "https://prod-185.westus.logic.azure.com:443/workflows/23ddbcdb47c94e77893973cc8cceb08c/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Y9CpXFG7vDr3Nb7a_CHhp7aTsam13fJMJTveVO92TIA",
    ),
    "welcome baby": os.getenv(
        "FLOW_URL_WELCOME_BABY",
        "https://prod-100.westus.logic.azure.com:443/workflows/2300d439983f40ccaef621dd012f982b/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=b5auB1lxGENLy-odC8Cxuil4XrXnHC-y7eajSgTwSvs",
    ),
    "dyad": os.getenv(
        "FLOW_URL_DYAD",
        "https://prod-153.westus.logic.azure.com:443/workflows/7e66478dcdba4d728005d3a6139975eb/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=2jSCZgv371CJjMworyXrnaKsK9jAN8ZxbiT__J2YuqU",
    ),
    "general united way": os.getenv(
        "FLOW_URL_GENERAL_UW",
        "https://prod-80.westus.logic.azure.com:443/workflows/ab041a615bc94e5b9175d3bbaf45dea5/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=EwZqtD99dV-5rlh6wpidvLaO2SjGdI2yhbzFo009oZc",
    ),
}
# ── rest of the file stays unchanged ──────────────────────────────────


# ──────────────────────────────────────────────────────────────────────
# 2)  Local SQLite
# ──────────────────────────────────────────────────────────────────────
DB_FILE = "submissions.db"


def init_db() -> None:
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


init_db()

# ──────────────────────────────────────────────────────────────────────
# Helper: send payload to a given Flow
# ──────────────────────────────────────────────────────────────────────
def send_to_flow(url: str, payload: dict) -> None:
    if not url:
        return
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        app.logger.warning("Post to %s failed: %s", url[:60] + "...", exc)


# ──────────────────────────────────────────────────────────────────────
# 3)  Routes
# ──────────────────────────────────────────────────────────────────────
@app.route("/")
def home() -> str:
    return render_template("home.html")


@app.route("/submit", methods=["POST"])
def submit_data():
    # --- collect & validate form fields ---
    volunteer_first_name = request.form.get("volunteer_first_name", "").strip()
    volunteer_last_name = request.form.get("volunteer_last_name", "").strip()
    volunteer_email = request.form.get("volunteer_email", "").strip()
    program_name_raw = request.form.get("program_name", "")
    event_activity_name = request.form.get("event_activity_name", "").strip()
    date_volunteered = request.form.get("date_volunteered", "").strip()
    volunteer_hours = request.form.get("volunteer_hours", "").strip()
    comments_feedback = request.form.get("comments_feedback", "").strip()
    shoutouts_highlights = request.form.get("shoutouts_highlights", "").strip()

    if not all(
        [
            volunteer_first_name,
            volunteer_last_name,
            volunteer_email,
            program_name_raw.strip(),
            event_activity_name,
            date_volunteered,
            volunteer_hours,
        ]
    ):
        return "Missing required fields.", 400

    # --- persist to SQLite ---
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
                volunteer_first_name,
                volunteer_last_name,
                volunteer_email,
                program_name_raw,
                event_activity_name,
                date_volunteered,
                volunteer_hours,
                comments_feedback,
                shoutouts_highlights,
            ),
        )

    # --- payload for Power Automate ---
    payload = {
        "volunteer_first_name": volunteer_first_name,
        "volunteer_last_name": volunteer_last_name,
        "volunteer_email": volunteer_email,
        "program_name": program_name_raw,
        "event_activity_name": event_activity_name,
        "date_volunteered": date_volunteered,
        "volunteer_hours": volunteer_hours,
        "comments_feedback": comments_feedback,
        "shoutouts_highlights": shoutouts_highlights,
    }

    # --- 1️⃣  Always post to the MAIN flow ---
    send_to_flow(FLOW_URL_MAIN, payload)

    # --- 2️⃣  Optionally post to a program-specific flow ---
    key = program_name_raw.strip().lower()
    send_to_flow(PROGRAM_TO_URL.get(key, ""), payload)

    return "Thank you! Your submission was recorded and sent to SharePoint."


# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
