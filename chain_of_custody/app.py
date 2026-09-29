"""Digital Forensics - Chain of Custody Management System (Flask + SQLite)."""
import sqlite3, hashlib, random, csv, io, os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, Response
from werkzeug.security import generate_password_hash as gph, check_password_hash as cph

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'forensics.db')
app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'forensic-demo-secret-key'
now = lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S')
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
ROLES = ['Admin', 'Investigator', 'Forensic Analyst', 'Evidence Custodian']
ACTIONS = ['Collected', 'Seized', 'Transferred', 'Examined', 'Stored', 'Submitted to Court', 'Returned']
ETYPES = ['Mobile', 'Laptop', 'Hard Disk', 'USB Drive', 'Email Evidence', 'Log File']

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT);
CREATE TABLE IF NOT EXISTS cases(case_id TEXT PRIMARY KEY,case_name TEXT,case_type TEXT,officer TEXT,created_date TEXT,status TEXT);
CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,case_id TEXT,name TEXT,type TEXT,description TEXT,
  collection_date TEXT,status TEXT,md5 TEXT,sha256 TEXT,content TEXT);
CREATE TABLE IF NOT EXISTS custody(log_id INTEGER PRIMARY KEY AUTOINCREMENT,evidence_id TEXT,from_person TEXT,to_person TEXT,
  transfer_date TEXT,transfer_time TEXT,location TEXT,action TEXT,remarks TEXT);
CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY AUTOINCREMENT,user_name TEXT,role TEXT,action TEXT,detail TEXT,timestamp TEXT);
"""

def q(sql, a=(), one=False, commit=False):
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    cur = c.execute(sql, a)
    if commit:
        c.commit(); out = cur.lastrowid
    else:
        rows = [dict(r) for r in cur.fetchall()]
        out = (rows[0] if rows else None) if one else rows
    c.close(); return out

def seed():
    c = sqlite3.connect(DB); c.executescript(SCHEMA); random.seed(42)
    F = "Aarav Priya Rohan Sneha Karthik Divya Arjun Meera Vikram Anjali Suresh Kavya Rahul Neha Imran Fatima David Sarah Manoj Lakshmi".split()
    L = "Sharma Iyer Nair Reddy Kumar Singh Das Menon Patel Khan Joseph Rao Verma Gupta Pillai".split()
    pw = gph('Password@123'); pref = {'Admin': 'admin', 'Investigator': 'investigator', 'Forensic Analyst': 'analyst', 'Evidence Custodian': 'custodian'}
    plan = ['Admin'] * 10 + ['Investigator'] * 15 + ['Forensic Analyst'] * 15 + ['Evidence Custodian'] * 10
    cnt = {}; people = {r: [] for r in ROLES}
    for i, r in enumerate(plan, 1):
        cnt[r] = cnt.get(r, 0) + 1; n = f"{F[i % 20]} {L[(i * 7) % 15]}"
        c.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)", (n, f"{pref[r]}{cnt[r]}@forensic.local", pw, r))
        people[r].append(n)
    CT = {'Mobile': ['Mobile Data Extraction', 'Suspect Phone Seizure', 'WhatsApp Fraud Probe', 'SIM Swap Investigation', 'Call Record Analysis'],
          'Email Phishing': ['Bank Phishing Campaign', 'CEO Fraud Email', 'Credential Harvesting', 'Fake Invoice Scam', 'Spear Phishing Attack'],
          'USB': ['Data Exfiltration via USB', 'Rogue USB Device', 'Insider Copy Incident', 'Malware USB Drop', 'Confidential File Leak'],
          'Laptop': ['Corporate Laptop Breach', 'Stolen Laptop Recovery', 'Employee Misuse Audit', 'Ransomware Laptop', 'Deleted Files Recovery'],
          'Hard Disk': ['Disk Image Analysis', 'Encrypted Drive Probe', 'Server Disk Forensics', 'Formatted Disk Recovery', 'Cloned Disk Verification']}
    EX = {'Mobile': ['Mobile', 'Log File', 'USB Drive'], 'Email Phishing': ['Email Evidence', 'Log File', 'Laptop'],
          'USB': ['USB Drive', 'Laptop', 'Log File'], 'Laptop': ['Laptop', 'Hard Disk', 'Log File'], 'Hard Disk': ['Hard Disk', 'Log File', 'Laptop']}
    DESC = {'Mobile': 'Smartphone seized; logical extraction of chats, call logs and media', 'Laptop': 'Laptop with full disk image and browser artifacts',
            'Hard Disk': 'SATA hard disk imaged with write blocker', 'USB Drive': 'USB flash drive holding suspicious files and autorun entries',
            'Email Evidence': 'Email headers and body preserved in EML format', 'Log File': 'Server/firewall/auth log export for the incident window'}
    CITY = "Chennai Mumbai Delhi Bengaluru Hyderabad Pune Kolkata Kochi Jaipur Ahmedabad".split()
    LOC = ['Crime Scene', 'Forensic Lab - Room 2', 'Evidence Locker A', 'Evidence Locker B', 'Police HQ', 'Cyber Cell Office', 'District Court', 'Digital Lab Vault']
    NEXT = {'Collected': 'Collected', 'Seized': 'Collected', 'Transferred': 'In Transit', 'Examined': 'Under Analysis',
            'Stored': 'In Storage', 'Submitted to Court': 'In Court', 'Returned': 'Returned'}
    e = 0; base = datetime(2025, 1, 5)
    for ci, (ct, names) in enumerate(CT.items()):
        for k in range(10):
            cid = f"CASE-{ci * 10 + k + 1:04d}"; cd = base + timedelta(days=ci * 40 + k * 4)
            officer = random.choice(people['Investigator'])
            c.execute("INSERT INTO cases VALUES(?,?,?,?,?,?)", (cid, f"{names[k % 5]} - {CITY[(k * 3 + ci) % 10]}", ct, officer, cd.strftime('%Y-%m-%d'),
                      random.choice(['Open', 'In Progress', 'Under Review', 'Closed'])))
            for et in EX[ct]:
                e += 1; eid = f"EVD-{e:04d}"; content = f"{eid}|{et}|SN{random.randint(10**7, 10**8)}|{random.getrandbits(64):x}"
                stored = content if e % 20 else content + "|MODIFIED"      # every 20th item is tampered (demo)
                c.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?)", (eid, cid, f"{et} #{e}", et, DESC[et], (cd + timedelta(days=1)).strftime('%Y-%m-%d'),
                          'Collected', md5(content), sha(content), stored))
                acts = ['Seized' if random.random() < .3 else 'Collected', 'Transferred', 'Examined', 'Stored', 'Submitted to Court', 'Returned'][:random.randint(2, 5)]
                who = officer; d = cd + timedelta(days=1)
                for a in acts:
                    to = random.choice(people['Forensic Analyst'] if a in ('Transferred', 'Examined') else people['Evidence Custodian'] if a in ('Stored', 'Returned') else people['Investigator'])
                    d += timedelta(days=random.randint(1, 6))
                    c.execute("INSERT INTO custody(evidence_id,from_person,to_person,transfer_date,transfer_time,location,action,remarks) VALUES(?,?,?,?,?,?,?,?)",
                              (eid, who, to, d.strftime('%Y-%m-%d'), f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}", random.choice(LOC), a, f"{a} - sealed bag, tag verified"))
                    who = to
                c.execute("UPDATE evidence SET status=? WHERE evidence_id=?", (NEXT[acts[-1]], eid))
    c.execute("INSERT INTO activity(user_name,role,action,detail,timestamp) VALUES('System','Admin','Database Seeded','Demo dataset loaded',?)", (now(),))
    c.commit(); c.close()

def log(action, detail=''):
    q("INSERT INTO activity(user_name,role,action,detail,timestamp) VALUES(?,?,?,?,?)",
      (session.get('name', '-'), session.get('role', '-'), action, detail, now()), commit=True)

def auth(f):
    @wraps(f)
    def w(*a, **k):
        if 'uid' not in session: return jsonify(error='Login required'), 401
        return f(*a, **k)
    return w

@app.route('/')
def index(): return app.send_static_file('index.html')

@app.post('/api/register')
def register():
    d = request.json or {}
    if not all(d.get(x) for x in ('name', 'email', 'password')) or d.get('role') not in ROLES: return jsonify(error='All fields required'), 400
    if q("SELECT 1 FROM users WHERE email=?", (d['email'].lower(),), one=True): return jsonify(error='Email already registered'), 400
    q("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)", (d['name'], d['email'].lower(), gph(d['password']), d['role']), commit=True)
    return jsonify(ok=True)

@app.post('/api/login')
def login():
    d = request.json or {}; u = q("SELECT * FROM users WHERE email=?", ((d.get('email') or '').lower(),), one=True)
    if not u or not cph(u['password'], d.get('password') or ''): return jsonify(error='Invalid email or password'), 401
    session.update(uid=u['user_id'], name=u['name'], role=u['role'], login_time=now()); log('User Login', u['email'])
    return jsonify(ok=True)

@app.post('/api/logout')
@auth
def logout():
    log('User Logout'); session.clear(); return jsonify(ok=True)

@app.get('/api/me')
@auth
def me(): return jsonify(name=session['name'], role=session['role'], login_time=session['login_time'])

@app.get('/api/stats')
@auth
def stats():
    n = lambda t: q(f"SELECT COUNT(*) c FROM {t}", one=True)['c']
    return jsonify(cases=n('cases'), evidence=n('evidence'), custody=n('custody'), users=n('users'))

KINDS = {'cases': ('case_id', ['case_id', 'case_name', 'case_type', 'officer', 'created_date', 'status'], 'status'),
         'evidence': ('evidence_id', ['evidence_id', 'case_id', 'name', 'type', 'description', 'collection_date', 'status', 'md5', 'sha256'], 'type'),
         'custody': ('log_id', ['log_id', 'evidence_id', 'from_person', 'to_person', 'transfer_date', 'transfer_time', 'location', 'action', 'remarks'], 'action'),
         'activity': ('id', ['id', 'user_name', 'role', 'action', 'detail', 'timestamp'], 'action')}

def fetch(kind, args):
    pk, cols, fc = KINDS[kind]; w, a = [], []
    if args.get('q'):
        w.append('(' + ' OR '.join(f'{c} LIKE ?' for c in cols) + ')'); a += [f"%{args['q']}%"] * len(cols)
    if args.get('f'): w.append(f'{fc}=?'); a.append(args['f'])
    if args.get('eid') and kind == 'custody': w.append('evidence_id=?'); a.append(args['eid'])
    if args.get('case') and kind == 'evidence': w.append('case_id=?'); a.append(args['case'])
    order = f'{pk} DESC' if kind == 'activity' else 'transfer_date,transfer_time,log_id' if kind == 'custody' and args.get('eid') else pk
    return q(f"SELECT {','.join(cols)} FROM {kind} {'WHERE ' + ' AND '.join(w) if w else ''} ORDER BY {order}", a)

@app.get('/api/<kind>')
@auth
def lst(kind):
    if kind not in KINDS: return jsonify(error='Not found'), 404
    return jsonify(fetch(kind, request.args))

@app.post('/api/cases')
@auth
def add_case():
    d = request.json; n = q("SELECT COUNT(*) c FROM cases", one=True)['c'] + 1
    cid = f"CASE-{n:04d}"
    while q("SELECT 1 FROM cases WHERE case_id=?", (cid,), one=True): n += 1; cid = f"CASE-{n:04d}"
    q("INSERT INTO cases VALUES(?,?,?,?,?,?)", (cid, d['case_name'], d['case_type'], d['officer'], d['created_date'], d['status']), commit=True)
    log('Case Created', cid); return jsonify(ok=True, id=cid)

@app.put('/api/cases/<cid>')
@auth
def upd_case(cid):
    d = request.json
    q("UPDATE cases SET case_name=?,case_type=?,officer=?,created_date=?,status=? WHERE case_id=?",
      (d['case_name'], d['case_type'], d['officer'], d['created_date'], d['status'], cid), commit=True)
    log('Case Updated', cid); return jsonify(ok=True)

@app.get('/api/evidence/<eid>')
@auth
def get_ev(eid):
    r = q("SELECT " + ','.join(KINDS['evidence'][1]) + " FROM evidence WHERE evidence_id=?", (eid,), one=True)
    return (jsonify(r) if r else (jsonify(error='Not found'), 404))

@app.post('/api/evidence')
@auth
def add_ev():
    d = request.json
    if not q("SELECT 1 FROM cases WHERE case_id=?", (d['case_id'],), one=True): return jsonify(error='Case ID does not exist'), 400
    n = q("SELECT COUNT(*) c FROM evidence", one=True)['c'] + 1; eid = f"EVD-{n:04d}"
    while q("SELECT 1 FROM evidence WHERE evidence_id=?", (eid,), one=True): n += 1; eid = f"EVD-{n:04d}"
    content = f"{eid}|{d['type']}|{d['name']}|{now()}"
    q("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?)", (eid, d['case_id'], d['name'], d['type'], d['description'], d['collection_date'], d['status'], md5(content), sha(content), content), commit=True)
    log('Evidence Added', eid); return jsonify(ok=True, id=eid)

@app.put('/api/evidence/<eid>')
@auth
def upd_ev(eid):
    d = request.json
    q("UPDATE evidence SET case_id=?,name=?,type=?,description=?,collection_date=?,status=? WHERE evidence_id=?",
      (d['case_id'], d['name'], d['type'], d['description'], d['collection_date'], d['status'], eid), commit=True)
    log('Evidence Updated', eid); return jsonify(ok=True)

@app.post('/api/evidence/<eid>/verify')
@auth
def verify(eid):
    r = q("SELECT content,md5,sha256 FROM evidence WHERE evidence_id=?", (eid,), one=True)
    if not r: return jsonify(error='Not found'), 404
    ok = md5(r['content']) == r['md5'] and sha(r['content']) == r['sha256']
    log('Integrity Verified', f"{eid}: {'Maintained' if ok else 'FAILED'}")
    return jsonify(ok=ok, stored_md5=r['md5'], current_md5=md5(r['content']), stored_sha256=r['sha256'], current_sha256=sha(r['content']))

@app.post('/api/custody')
@auth
def add_cust():
    d = request.json
    if not q("SELECT 1 FROM evidence WHERE evidence_id=?", (d['evidence_id'],), one=True): return jsonify(error='Evidence ID does not exist'), 400
    q("INSERT INTO custody(evidence_id,from_person,to_person,transfer_date,transfer_time,location,action,remarks) VALUES(?,?,?,?,?,?,?,?)",
      (d['evidence_id'], d['from_person'], d['to_person'], d['transfer_date'], d['transfer_time'], d['location'], d['action'], d.get('remarks', '')), commit=True)
    log('Custody Transfer Created', f"{d['evidence_id']}: {d['action']}"); return jsonify(ok=True)

@app.get('/api/report/<kind>/<fmt>')
@auth
def report(kind, fmt):
    if kind not in ('cases', 'evidence', 'custody'): return jsonify(error='Not found'), 404
    rows = fetch(kind, {}); cols = list(rows[0].keys()); stamp = datetime.now().strftime('%Y%m%d_%H%M')
    if fmt == 'csv':
        s = io.StringIO(); w = csv.writer(s); w.writerow(cols); w.writerows([r.values() for r in rows])
        return Response(s.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={kind}_report_{stamp}.csv'})
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    if kind == 'evidence': cols = [c for c in cols if c not in ('description', 'sha256')]
    buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    st = getSampleStyleSheet()
    data = [[c.replace('_', ' ').title() for c in cols]] + [[str(r[c])[:34] for c in cols] for r in rows]
    t = Table(data, repeatRows=1); t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b3d5c')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 6.5), ('GRID', (0, 0), (-1, -1), .25, colors.grey), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eef4f8')])]))
    doc.build([Paragraph(f"Chain of Custody System - {kind.title()} Report", st['Title']),
               Paragraph(f"Generated {now()} by {session['name']} ({session['role']}) - {len(rows)} records", st['Normal']), Spacer(1, 8), t])
    log('Report Exported', f'{kind} PDF')
    return Response(buf.getvalue(), mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename={kind}_report_{stamp}.pdf'})

if not os.path.exists(DB): seed()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)