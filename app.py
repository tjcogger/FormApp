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
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/31/workflows/7a0e4f601d6e4dfaa1423b3d921746ef/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=wD5cXJLz03Bsvtb8uw6CWlkE2eZ5N1derO1JlFfW5a0",
    ),
    "collective impact": os.getenv(
        "FLOW_URL_COLLECTIVE_IMPACT",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/18/workflows/fc073cd921ed4a45a11df5a386f82cee/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=S6xdzFWdAwsxWHXToO-P2w6ritbII5wnekC61h9yoNU",
    ),
    "learn with playgroup": os.getenv(
        "FLOW_URL_LEARN_WITH_PLAYGROUP",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/05/workflows/a6aad79b686345a8b3f8bd8782b4f337/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=1oNOzrV-0W4LbviVdtFX9ntL8H1-6_Eo9QFFX5qv1dk",
    ),
    "little neighborhood libraries": os.getenv(
        "FLOW_URL_LITTLE_LIBRARIES",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/11/workflows/d108c90980684890a6949af372f533cc/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=pj4ga7etya2uSEFPHFqZsenR6VE7cus18TxeJkkQKB0",
    ),
    "nonprofit connection": os.getenv(
        "FLOW_URL_NONPROFIT_CONNECTION",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/22/workflows/d91ecd30269b451dbdabc813155df949/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=e76Rv8eqIM8AHGxNjlln_TW89GPxn_7nRS0VnwfgsBQ",
    ),
    "student success program": os.getenv(
        "FLOW_URL_STUDENT_SUCCESS",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/01/workflows/c77785cb0fa54209acfef52a8e2cfb27/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=qETqd1a56up4y7xNWIPXcCd48Q3d2RrpdKKnchtK90g",
    ),
    "weber ctc": os.getenv(
        "FLOW_URL_WEBER_CTC",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/14/workflows/23ddbcdb47c94e77893973cc8cceb08c/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=IVLdRZckZPMPcG_Pj0jHjmeNeNZoyrCPNARd76Cgit0",
    ),
    "welcome baby": os.getenv(
        "FLOW_URL_WELCOME_BABY",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/15/workflows/2300d439983f40ccaef621dd012f982b/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=7gmFFPCZwbtERDqf0RoFJvtVzXeuFXSm8swuA93Ifmg",
    ),
    "dyad": os.getenv(
        "FLOW_URL_DYAD",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/21/workflows/7e66478dcdba4d728005d3a6139975eb/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=FkQSusRHti2KX8ehwEx_0nlBmcTC_X1_HocdFeJa4E8",
    ),
    "general united way": os.getenv(
        "FLOW_URL_GENERAL_UW",
        "https://default55c9796cbfbf49fd8847d22bc37290.81.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/31/workflows/ab041a615bc94e5b9175d3bbaf45dea5/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=PYRKfCixc3hFOENljP4ITcBgJK-0EkroeucSWUudzlA",
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
