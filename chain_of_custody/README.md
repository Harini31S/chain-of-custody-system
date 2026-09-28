# Digital Forensics – Chain of Custody Management System
College DBMS mini-project. Flask + SQLite + vanilla HTML/CSS/JS. Runs fully offline.

## Setup
```
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 (a pre-populated `forensics.db` is included; delete it to re-seed automatically).

## Demo logins (password for all seeded users: `Password@123`)
| Role | Emails |
|---|---|
| Admin (10) | admin1@forensic.local … admin10@forensic.local |
| Investigator (15) | investigator1 … investigator15 @forensic.local |
| Forensic Analyst (15) | analyst1 … analyst15 @forensic.local |
| Evidence Custodian (10) | custodian1 … custodian10 @forensic.local |

## Data
50 users, 50 cases (10 each: Mobile, Email Phishing, USB, Laptop, Hard Disk), 150 evidence items, ~500 custody logs.
Every 20th evidence item (e.g. EVD-0020) is deliberately tampered so **Verify Integrity** shows *Integrity Failed*; the rest show *Integrity Maintained*.

## Structure
```
chain_of_custody/
├── app.py          # Flask API, SQLite schema, seeding, reports (CSV/PDF)
├── forensics.db    # Prepopulated database
├── requirements.txt
├── README.md
└── static/  index.html · style.css · app.js
```
## Notes
Integrity: MD5/SHA-256 are stored at collection time; verification recomputes them from the stored evidence content and compares.
Passwords are hashed (werkzeug). Demo only – change `secret_key` for any real use.
