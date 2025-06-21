# -*- coding: utf-8 -*-
"""
Volunteer submission form → SQLite backup → SharePoint via Power Automate
Now routes to 10 program-specific flows (plus a default).
"""

import os
import sqlite3
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# ──────────────────────────────────────────────────────────────────────
# 1)  Power Automate web-hook URLs
#     (env-vars preferred; literals are fallbacks for local testing)
# ──────────────────────────────────────────────────────────────────────
FLOW_URL_MAIN = os.getenv(
    "FLOW_URL_MAIN",
    "https://prod-35.westus.logic.azure.com:443/workflows/37c3bf8a61df45c4b2e4de82e1e932c5/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=mjOa4NAb6ZnH_D1dvtDE3-Xb7MdPfkp0wgO926jdh3I",
)

FLOW_URL_211 = os.getenv(
    "FLOW_URL_211",
    "https://prod-143.westus.logic.azure.com:443/workflows/7a0e4f601d6e4dfaa1423b3d921746ef/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=nZJo1sU2uucPTPgQdCiICxOcbDdQyzMO2LG9N22feqY",
)

FLOW_URL_COLLECTIVE_IMPACT = os.getenv(
    "FLOW_URL_COLLECTIVE_IMPACT",
    "https://prod-70.westus.logic.azure.com:443/workflows/151a3f5b122048a9bfd33400666dd327/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=mzzDEAnuAkjljm7j2uFnJLVz7J-849pwM47o7M1aD2o",
)

FLOW_URL_LEARN_WITH_PLAYGROUP = os.getenv(
    "FLOW_URL_LEARN_WITH_PLAYGROUP",
    "https://prod-139.westus.logic.azure.com:443/workflows/92f37cb44a8e464983226f2557e48ee5/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=lj5noYv7_T5zbs7CYGkzAnQyTpheGPpfno7jk0MmL0g",
)

FLOW_URL_LITTLE_LIBRARIES = os.getenv(
    "FLOW_URL_LITTLE_LIBRARIES",
    "https://prod-129.westus.logic.azure.com:443/workflows/f6e9aa49d6704ef2864b13bf3487d28b/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=gEQ_XpD-_z_caQuiZFJghbZwzKEvG_ZH2_1pJ02HCMQ",
)

FLOW_URL_NONPROFIT_CONNECTION = os.getenv(
    "FLOW_URL_NONPROFIT_CONNECTION",
    "https://prod-73.westus.logic.azure.com:443/workflows/ad077a2d6391415b82a2f6b3aacee40c/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=soKi_3FPjRoM6op0CMLXdG4uYgN8irEFnow88wg-T3k",
)

FLOW_URL_STUDENT_SUCCESS = os.getenv(
    "FLOW_URL_STUDENT_SUCCESS",
    "https://prod-186.westus.logic.azure.com:443/workflows/527df460eb6b4e309a8eed5f64db4977/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=-IeE6_9IrUjAeuowTrAcvI6M5WwY-xsaZO0QiI7_IdM",
)

FLOW_URL_WEBER_CTC = os.getenv(
    "FLOW_URL_WEBER_CTC",
    "https://prod-13.westus.logic.azure.com:443/workflows/4747d0390a0c4040b979b9953fd7097c/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=FHLXRDejJfF6VIbMomGIMqK2fKcgJ4lDAXXkJdRkwLo",
)

FLOW_URL_WELCOME_BABY = os.getenv(
    "FLOW_URL_WELCOME_BABY",
    "https://prod-73.westus.logic.azure.com:443/workflows/334530580fbe47da804ab9967f024d75/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=l5ZkTYUT0u8Lp23Qx_UF8b3-eRhwLChvOZmkSltjCZg",
)

FLOW_URL_DYAD = os.getenv(
    "FLOW_URL_DYAD",
    "https://prod-13.westus.logic.azure.com:443/workflows/184291dc186c4737ab975a3f5a3e004e/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=t6Yw6dBBOsPnSYhVcQNmsQPaIo-Di_iOr1YdcTfsM_c",
)

FLOW_URL_GENERAL_UW = os.getenv(
    "FLOW_URL_GENERAL_UW",
    "https://prod-167.westus.logic.azure.com:443/workflows/1564327b17d44fadac443422d22a612e/"
    "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&"
    "sv=1.0&sig=coYHDUvPEIIplQnVLE8zdfVpL-W8xMM-09IONv9juR8",
)

# ──────────────────────────────────────────────────────────────────────
# 2)  Local SQLite settings
# ──────────────────────────────────────────────────────────────────────
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


init_db()

# ──────────────────────────────────────────────────────────────────────
# 3)  Routes
# ──────────────────────────────────────────────────────────────────────
@app.route("/")
def home() -> str:
    return render_template("home.html")


@app.route("/submit", methods=["POST"])
def submit_data():
    # --- pull & trim fields ---
    volunteer_first_name = request.form.get("volunteer_first_name", "").strip()
    volunteer_last_name  = request.form.get("volunteer_last_name", "").strip()
    volunteer_email      = request.form.get("volunteer_email", "").strip()
    program_name_raw     = request.form.get("program_name", "")
    event_activity_name  = request.form.get("event_activity_name", "").strip()
    date_volunteered     = request.form.get("date_volunteered", "").strip()
    volunteer_hours      = request.form.get("volunteer_hours", "").strip()
    comments_feedback    = request.form.get("comments_feedback", "").strip()
    shoutouts_highlights = request.form.get("shoutouts_highlights", "").strip()

    program_name = program_name_raw.strip().lower()   # for routing look-up

    # --- basic validation ---
    if not all(
        [
            volunteer_first_name,
            volunteer_last_name,
            volunteer_email,
            program_name,
            event_activity_name,
            date_volunteered,
            volunteer_hours,
        ]
    ):
        return "Missing required fields.", 400

    # --- save locally ---
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

    # --- choose the correct Flow URL ---
    if program_name == "211" or program_name.startswith("211 "):
        target_url = FLOW_URL_211

    elif program_name == "collective impact":
        target_url = FLOW_URL_COLLECTIVE_IMPACT

    elif program_name == "learn with playgroup":
        target_url = FLOW_URL_LEARN_WITH_PLAYGROUP

    elif program_name == "little neighborhood libraries":
        target_url = FLOW_URL_LITTLE_LIBRARIES

    elif program_name == "nonprofit connection":
        target_url = FLOW_URL_NONPROFIT_CONNECTION

    elif program_name == "student success program":
        target_url = FLOW_URL_STUDENT_SUCCESS

    elif program_name == "weber ctc":
        target_url = FLOW_URL_WEBER_CTC

    elif program_name == "welcome baby":
        target_url = FLOW_URL_WELCOME_BABY

    elif program_name == "dyad":
        target_url = FLOW_URL_DYAD

    elif program_name == "general united way":
        target_url = FLOW_URL_GENERAL_UW

    else:
        target_url = FLOW_URL_MAIN  # default / fallback

    # --- send to Power Automate ---
    payload = {
        "volunteer_first_name": volunteer_first_name,
        "volunteer_last_name":  volunteer_last_name,
        "volunteer_email":      volunteer_email,
        "program_name":         program_name_raw,
        "event_activity_name":  event_activity_name,
        "date_volunteered":     date_volunteered,
        "volunteer_hours":      volunteer_hours,
        "comments_feedback":    comments_feedback,
        "shoutouts_highlights": shoutouts_highlights,
    }

    try:
        response = requests.post(target_url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print("Error posting to Power Automate:", exc)
        return (
            "Saved locally, but we couldn’t send it to SharePoint. Please notify IT.",
            502,
        )

    return "Thank you! Your submission was recorded and sent to SharePoint."


# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
