from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import sqlite3
from functools import wraps
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "VolunteerConnect-College-Demo-2026"
DATABASE = "volunteerconnect.db"


def now():
    return datetime.now().isoformat(timespec="seconds")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def table_columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS volunteers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        skills TEXT,
        availability TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        organization_type TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        organization TEXT NOT NULL,
        description TEXT,
        required_skills TEXT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        volunteer_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(volunteer_id, opportunity_id),
        FOREIGN KEY(volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE,
        FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        volunteer_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
        created_at TEXT NOT NULL,
        UNIQUE(volunteer_id, opportunity_id, date),
        FOREIGN KEY(volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE,
        FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()


def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.after_request(no_cache)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def event_status(event_date):
    try:
        d = datetime.strptime(event_date, "%Y-%m-%d").date()
        if d < date.today(): return "Completed"
        if d == date.today(): return "Today"
        return "Upcoming"
    except ValueError:
        return "Unknown"


def badge(status):
    cls = {"Upcoming":"upcoming", "Today":"today", "Completed":"completed"}.get(status, "completed")
    return f'<span class="badge {cls}">{status}</span>'


def layout(title, body):
    nav = ""
    if "user_id" in session:
        nav += '<a href="/">Home</a><a href="/dashboard">Dashboard</a><a href="/opportunities">Opportunities</a>'
        if session.get("role") == "organization":
            nav += '<a href="/create-opportunity">Create Opportunity</a><a href="/matches">Smart Matching</a><a href="/schedules">Schedules</a><a href="/attendance">Attendance</a><a href="/completed-events">Completed Events</a><a href="/database">Database</a>'
        else:
            nav += '<a href="/schedules">My Schedules</a><a href="/completed-events">Completed Events</a>'
        nav += '<a class="logout" href="/logout">Logout</a>'
    else:
        nav = '<a href="/">Home</a><a href="/login">Login</a><a href="/register">Register</a>'
    flashes = "".join(f'<div class="flash {cat}">{msg}</div>' for cat, msg in session.pop("_flashes", []))
    return f'''<!doctype html><html><head><title>{title} - VolunteerConnect</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b1120;color:#e5e7eb;font-family:Arial,sans-serif}}a{{color:#93c5fd}}.navbar{{position:sticky;top:0;z-index:10;background:#111827;border-bottom:1px solid #263244;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}}.brand{{font-size:22px;font-weight:700;color:#60a5fa}}.navlinks{{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}}.navlinks a{{text-decoration:none;padding:8px 10px;border-radius:7px;font-size:13px;color:#dbeafe}}.navlinks a:hover{{background:#1e3a5f}}.logout{{background:#dc2626!important;color:#fff!important}}.container{{width:94%;max-width:1200px;margin:30px auto}}.hero{{padding:42px;border-radius:18px;background:linear-gradient(135deg,#172554,#1e3a8a);margin-bottom:25px}}h1{{font-size:34px}}h2{{color:#93c5fd}}.hero h1{{font-size:40px;margin:0 0 10px}}.hero p{{font-size:18px;color:#dbeafe}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}}.card,.stat{{background:#111827;border:1px solid #263244;border-radius:14px;padding:22px;margin-bottom:18px}}.stat-number{{font-size:34px;font-weight:700;color:#60a5fa}}.stat-title{{color:#9ca3af;margin-top:5px}}input,textarea,select{{width:100%;padding:12px;margin:7px 0 16px;background:#0f172a;border:1px solid #374151;color:#fff;border-radius:8px}}textarea{{min-height:100px;resize:vertical}}label{{font-weight:700;color:#d1d5db}}button,.btn{{display:inline-block;background:#2563eb;color:#fff;border:0;border-radius:8px;padding:10px 16px;text-decoration:none;cursor:pointer;margin:4px;font-size:14px}}button:hover,.btn:hover{{background:#1d4ed8}}.green{{background:#16a34a!important}}.red{{background:#dc2626!important}}.purple{{background:#7c3aed!important}}.gray{{background:#4b5563!important}}table{{width:100%;border-collapse:collapse;min-width:700px}}th,td{{padding:11px;border-bottom:1px solid #374151;text-align:left;vertical-align:top}}th{{background:#1e293b;color:#93c5fd}}.table-wrap{{overflow-x:auto}}.badge{{display:inline-block;padding:5px 10px;border-radius:20px;font-size:12px;font-weight:700}}.upcoming{{background:#14532d;color:#bbf7d0}}.today{{background:#713f12;color:#fef08a}}.completed{{background:#334155;color:#cbd5e1}}.match{{font-weight:700;color:#4ade80;font-size:20px}}.flash{{padding:12px;border-radius:8px;margin-bottom:12px;background:#1e3a8a}}.danger{{background:#7f1d1d}}.warning{{background:#713f12}}.success{{background:#14532d}}.empty{{text-align:center;padding:40px;color:#9ca3af}}.small{{font-size:13px;color:#9ca3af}}.footer{{text-align:center;color:#6b7280;padding:30px}}@media(max-width:800px){{.navbar{{flex-direction:column;align-items:flex-start}}.hero h1{{font-size:30px}}}}
</style></head><body><nav class="navbar"><div class="brand">VolunteerConnect</div><div class="navlinks">{nav}</div></nav><main class="container">{flashes}{body}</main><footer class="footer">VolunteerConnect | Volunteer Matching & Scheduling Platform</footer></body></html>'''


@app.route("/")
def home():
    if "user_id" in session: return redirect(url_for("dashboard"))
    return layout("Home", '''<div class="hero"><h1>VolunteerConnect</h1><p>Volunteer Matching and Scheduling Platform connecting volunteers with organizations and meaningful community opportunities.</p><a class="btn" href="/login">Login</a><a class="btn green" href="/register">Get Started</a></div><div class="grid"><div class="card"><h2>🤝 Smart Matching</h2><p>Match volunteers to events based on skills.</p></div><div class="card"><h2>📅 Scheduling</h2><p>Schedule volunteers for events.</p></div><div class="card"><h2>✅ Attendance</h2><p>Record Present or Absent attendance.</p></div><div class="card"><h2>📊 Management</h2><p>Organizations can create and manage opportunities.</p></div></div>''')


@app.route("/register")
def register():
    return layout("Register", '''<div class="card"><h2>Create Account</h2><p>Select your role.</p><a class="btn" href="/register/volunteer">Register as Volunteer</a><a class="btn purple" href="/register/organization">Register as Organization</a></div>''')


@app.route("/register/volunteer", methods=["GET","POST"])
def register_volunteer():
    if request.method == "POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); phone=request.form.get("phone","").strip(); skills=request.form.get("skills","").strip(); availability=request.form.get("availability","").strip(); password=request.form.get("password","")
        if not name or not email or not password:
            flash("Name, email and password are required.","warning"); return redirect(url_for("register_volunteer"))
        conn=get_db_connection()
        try:
            cur=conn.cursor(); ts=now(); cur.execute("INSERT INTO users(role,email,password_hash,created_at) VALUES(?,?,?,?)",("volunteer",email,generate_password_hash(password),ts)); uid=cur.lastrowid
            cur.execute("INSERT INTO volunteers(user_id,name,email,phone,skills,availability,created_at) VALUES(?,?,?,?,?,?,?)",(uid,name,email,phone,skills,availability,ts)); conn.commit()
            flash("Volunteer account created successfully.","success"); return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.rollback(); flash("Email already registered.","danger")
        finally: conn.close()
    return layout("Volunteer Registration", '''<div class="card"><h2>Volunteer Registration</h2><form method="POST" autocomplete="off"><label>Full Name</label><input name="name" autocomplete="off" required><label>Email</label><input type="email" name="email" autocomplete="off" required><label>Phone</label><input name="phone" autocomplete="off"><label>Skills</label><input name="skills" placeholder="communication, management, first aid" autocomplete="off"><label>Availability</label><input name="availability" placeholder="Weekends, 10 AM - 5 PM" autocomplete="off"><label>Password</label><input type="password" name="password" autocomplete="new-password" required><button>Create Volunteer Account</button></form></div>''')


@app.route("/register/organization", methods=["GET","POST"])
def register_organization():
    if request.method == "POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); phone=request.form.get("phone","").strip(); address=request.form.get("address","").strip(); org_type=request.form.get("organization_type","").strip(); password=request.form.get("password","")
        if not name or not email or not password:
            flash("Organization name, email and password are required.","warning"); return redirect(url_for("register_organization"))
        conn=get_db_connection()
        try:
            cur=conn.cursor(); ts=now(); cur.execute("INSERT INTO users(role,email,password_hash,created_at) VALUES(?,?,?,?)",("organization",email,generate_password_hash(password),ts)); uid=cur.lastrowid
            cur.execute("INSERT INTO organizations(user_id,name,email,phone,address,organization_type,created_at) VALUES(?,?,?,?,?,?,?)",(uid,name,email,phone,address,org_type,ts)); conn.commit()
            flash("Organization account created successfully.","success"); return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.rollback(); flash("Email already registered.","danger")
        finally: conn.close()
    return layout("Organization Registration", '''<div class="card"><h2>Organization Registration</h2><form method="POST" autocomplete="off"><label>Organization Name</label><input name="name" autocomplete="off" required><label>Email</label><input type="email" name="email" autocomplete="off" required><label>Phone</label><input name="phone" autocomplete="off"><label>Address</label><textarea name="address" autocomplete="off"></textarea><label>Organization Type</label><select name="organization_type"><option>NGO</option><option>College</option><option>Hospital</option><option>Community</option><option>Other</option></select><label>Password</label><input type="password" name="password" autocomplete="new-password" required><button>Create Organization Account</button></form></div>''')


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        conn=get_db_connection(); user=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); conn.close()
        if user and check_password_hash(user["password_hash"],password):
            session.clear(); session["user_id"]=user["id"]; session["role"]=user["role"]; session["email"]=user["email"]; flash("Login successful.","success"); return redirect(url_for("dashboard"))
        flash("Invalid email or password.","danger")
    return layout("Login", '''<div class="card"><h2>Login</h2><form method="POST" autocomplete="off"><label>Email</label><input type="email" name="email" autocomplete="off" required><label>Password</label><input type="password" name="password" autocomplete="new-password" required><button>Login</button></form><p class="small">Don't have an account? <a href="/register">Register here</a></p></div>''')


@app.route("/logout")
def logout():
    session.clear(); flash("You have been logged out.","success"); return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn=get_db_connection(); role=session["role"]
    if role=="volunteer":
        v=conn.execute("SELECT * FROM volunteers WHERE user_id=?",(session["user_id"],)).fetchone()
        if not v: conn.close(); flash("Volunteer profile not found.","danger"); return redirect(url_for("logout"))
        rows=conn.execute("SELECT s.*,o.title,o.organization FROM schedules s JOIN opportunities o ON s.opportunity_id=o.id WHERE s.volunteer_id=?",(v["id"],)).fetchall(); conn.close()
        upcoming=sum(event_status(r["date"])!="Completed" for r in rows); completed=sum(event_status(r["date"])=="Completed" for r in rows)
        body=f'''<div class="hero"><h1>Volunteer Dashboard</h1><p>Welcome, <strong>{v["name"]}</strong>.</p></div><div class="grid"><div class="stat"><div class="stat-number">{upcoming}</div><div class="stat-title">Upcoming Events</div></div><div class="stat"><div class="stat-number">{completed}</div><div class="stat-title">Completed Events</div></div><div class="stat"><div class="stat-number">{len(rows)}</div><div class="stat-title">Total Schedules</div></div></div><div class="card"><h2>Quick Actions</h2><a class="btn" href="/opportunities">Browse Opportunities</a><a class="btn green" href="/schedules">My Schedules</a><a class="btn gray" href="/completed-events">Completed Events</a></div>'''
    else:
        o=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone()
        if not o: conn.close(); flash("Organization profile not found.","danger"); return redirect(url_for("logout"))
        events=conn.execute("SELECT * FROM opportunities WHERE organization_id=?",(o["id"],)).fetchall(); schedules=conn.execute("SELECT COUNT(*) FROM schedules s JOIN opportunities p ON s.opportunity_id=p.id WHERE p.organization_id=?",(o["id"],)).fetchone()[0]; vc=conn.execute("SELECT COUNT(*) FROM volunteers").fetchone()[0]; oc=conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]; conn.close()
        upcoming=sum(event_status(e["date"])!="Completed" for e in events); completed=sum(event_status(e["date"])=="Completed" for e in events)
        body=f'''<div class="hero"><h1>Organization Dashboard</h1><p>Welcome, <strong>{o["name"]}</strong>.</p></div><div class="grid"><div class="stat"><div class="stat-number">{upcoming}</div><div class="stat-title">Upcoming Events</div></div><div class="stat"><div class="stat-number">{completed}</div><div class="stat-title">Completed Events</div></div><div class="stat"><div class="stat-number">{schedules}</div><div class="stat-title">Scheduled Volunteers</div></div><div class="stat"><div class="stat-number">{vc}</div><div class="stat-title">Registered Volunteers</div></div><div class="stat"><div class="stat-number">{oc}</div><div class="stat-title">Organizations</div></div></div><div class="card"><h2>Quick Actions</h2><a class="btn" href="/create-opportunity">Create Opportunity</a><a class="btn purple" href="/matches">Smart Matching</a><a class="btn green" href="/schedules">Schedules</a><a class="btn" href="/attendance">Attendance</a><a class="btn gray" href="/completed-events">Completed Events</a><a class="btn" href="/database">Database</a></div>'''
    return layout("Dashboard",body)


@app.route("/opportunities")
@login_required
def opportunities():
    conn=get_db_connection(); rows=conn.execute("SELECT * FROM opportunities ORDER BY date,time").fetchall(); conn.close()
    if not rows: return layout("Opportunities",'<div class="card empty"><h2>No Opportunities Available</h2><p>Organizations have not created any opportunities yet.</p></div>')
    cards=""
    for r in rows:
        cards+=f'''<div class="card"><h2>{r["title"]}</h2><p><strong>Organization:</strong> {r["organization"]}</p><p><strong>Description:</strong> {r["description"] or "-"}</p><p><strong>Required Skills:</strong> {r["required_skills"] or "-"}</p><p><strong>Date:</strong> {r["date"]} &nbsp; <strong>Time:</strong> {r["time"]}</p>{badge(event_status(r["date"]))}</div>'''
    return layout("Opportunities",f"<h1>Volunteer Opportunities</h1>{cards}")


@app.route("/create-opportunity", methods=["GET","POST"])
@role_required("organization")
def create_opportunity():
    conn=get_db_connection(); org=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone()
    if request.method=="POST":
        title=request.form.get("title","").strip(); desc=request.form.get("description","").strip(); skills=request.form.get("required_skills","").strip(); event_date=request.form.get("date",""); event_time=request.form.get("time","")
        if not title or not event_date or not event_time:
            conn.close(); flash("Title, date and time are required.","warning"); return redirect(url_for("create_opportunity"))
        try: datetime.strptime(event_date,"%Y-%m-%d")
        except ValueError:
            conn.close(); flash("Please enter a valid date.","danger"); return redirect(url_for("create_opportunity"))
        conn.execute("INSERT INTO opportunities(organization_id,title,organization,description,required_skills,date,time,created_at) VALUES(?,?,?,?,?,?,?,?)",(org["id"],title,org["name"],desc,skills,event_date,event_time,now())); conn.commit(); conn.close(); flash("Opportunity created successfully.","success"); return redirect(url_for("opportunities"))
    conn.close()
    return layout("Create Opportunity",'''<div class="card"><h2>Create Volunteer Opportunity</h2><form method="POST" autocomplete="off"><label>Opportunity Title</label><input name="title" placeholder="Blood Donation Camp" autocomplete="off" required><label>Description</label><textarea name="description" autocomplete="off" placeholder="Describe the event..."></textarea><label>Required Skills</label><input name="required_skills" placeholder="communication, management, first aid" autocomplete="off"><label>Event Date</label><input type="date" name="date" required><label>Event Time</label><input type="time" name="time" required><button>Create Opportunity</button></form></div>''')


@app.route("/matches")
@role_required("organization")
def matches():
    conn=get_db_connection(); org=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone(); opps=conn.execute("SELECT * FROM opportunities WHERE organization_id=? ORDER BY date",(org["id"],)).fetchall(); selected=request.args.get("opportunity_id")
    if not selected:
        conn.close(); options=''.join(f'<option value="{o["id"]}">{o["title"]} - {o["date"]}</option>' for o in opps); return layout("Smart Matching",f'''<div class="card"><h2>Smart Volunteer Matching</h2><p>Select an opportunity.</p><form method="GET"><select name="opportunity_id" required><option value="">-- Select Opportunity --</option>{options}</select><button>Find Matches</button></form></div>''')
    opp=conn.execute("SELECT * FROM opportunities WHERE id=? AND organization_id=?",(selected,org["id"])).fetchone(); volunteers=conn.execute("SELECT * FROM volunteers ORDER BY name").fetchall(); conn.close()
    if not opp: flash("Opportunity not found.","danger"); return redirect(url_for("matches"))
    required={s.strip().lower() for s in (opp["required_skills"] or "").split(",") if s.strip()}; results=[]
    for v in volunteers:
        skills={s.strip().lower() for s in (v["skills"] or "").split(",") if s.strip()}; matched=sorted(required & skills); score=round(len(matched)/len(required)*100) if required else 0; results.append((score,v,matched))
    results.sort(key=lambda x:(x[0],x[1]["name"]),reverse=True)
    rows=''
    for score,v,matched in results:
        rows+=f'''<tr><td>{v["name"]}</td><td>{v["email"]}</td><td>{v["skills"] or "-"}</td><td>{", ".join(matched) or "No exact match"}</td><td><span class="match">{score}%</span></td><td><form method="POST" action="/schedule/{v["id"]}/{opp["id"]}"><button class="green">Schedule</button></form></td></tr>'''
    return layout("Smart Matching",f'''<div class="card"><h2>Smart Matching</h2><p><strong>Opportunity:</strong> {opp["title"]}</p><p><strong>Required Skills:</strong> {opp["required_skills"] or "None"}</p></div><div class="card"><div class="table-wrap"><table><tr><th>Volunteer</th><th>Email</th><th>Skills</th><th>Matched Skills</th><th>Score</th><th>Action</th></tr>{rows}</table></div></div>''')


@app.route("/schedule/<int:volunteer_id>/<int:opportunity_id>", methods=["POST"])
@role_required("organization")
def schedule_volunteer(volunteer_id,opportunity_id):
    conn=get_db_connection(); org=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone(); opp=conn.execute("SELECT * FROM opportunities WHERE id=? AND organization_id=?",(opportunity_id,org["id"])).fetchone(); v=conn.execute("SELECT * FROM volunteers WHERE id=?",(volunteer_id,)).fetchone()
    if not opp or not v: conn.close(); flash("Invalid volunteer or opportunity.","danger"); return redirect(url_for("matches"))
    exists=conn.execute("SELECT id FROM schedules WHERE volunteer_id=? AND opportunity_id=?",(volunteer_id,opportunity_id)).fetchone()
    if exists: conn.close(); flash(f'{v["name"]} is already scheduled for this event.',"warning"); return redirect(url_for("matches",opportunity_id=opportunity_id))
    conn.execute("INSERT INTO schedules(volunteer_id,opportunity_id,date,time,created_at) VALUES(?,?,?,?,?)",(volunteer_id,opportunity_id,opp["date"],opp["time"],now())); conn.commit(); conn.close(); flash(f'{v["name"]} scheduled successfully.',"success"); return redirect(url_for("matches",opportunity_id=opportunity_id))


@app.route("/schedules")
@login_required
def schedules():
    conn=get_db_connection()
    if session["role"]=="organization":
        org=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone(); rows=conn.execute("SELECT s.*,v.name volunteer_name,v.email volunteer_email,o.title,o.organization FROM schedules s JOIN volunteers v ON s.volunteer_id=v.id JOIN opportunities o ON s.opportunity_id=o.id WHERE o.organization_id=? ORDER BY s.date,s.time",(org["id"],)).fetchall(); title="Schedules"; header='<tr><th>Volunteer</th><th>Email</th><th>Opportunity</th><th>Date</th><th>Time</th><th>Status</th></tr>'; body=''.join(f'<tr><td>{r["volunteer_name"]}</td><td>{r["volunteer_email"]}</td><td>{r["title"]}</td><td>{r["date"]}</td><td>{r["time"]}</td><td>{badge(event_status(r["date"]))}</td></tr>' for r in rows)
    else:
        v=conn.execute("SELECT * FROM volunteers WHERE user_id=?",(session["user_id"],)).fetchone(); rows=conn.execute("SELECT s.*,o.title,o.organization FROM schedules s JOIN opportunities o ON s.opportunity_id=o.id WHERE s.volunteer_id=? ORDER BY s.date,s.time",(v["id"],)).fetchall(); title="My Schedules"; header='<tr><th>Opportunity</th><th>Organization</th><th>Date</th><th>Time</th><th>Status</th></tr>'; body=''.join(f'<tr><td>{r["title"]}</td><td>{r["organization"]}</td><td>{r["date"]}</td><td>{r["time"]}</td><td>{badge(event_status(r["date"]))}</td></tr>' for r in rows)
    conn.close()
    if not rows: return layout(title,'<div class="card empty"><h2>No Schedules Found</h2></div>')
    return layout(title,f'<div class="card"><h2>{title}</h2><div class="table-wrap"><table>{header}{body}</table></div></div>')


@app.route("/attendance")
@role_required("organization")
def attendance():
    conn=get_db_connection(); org=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone(); rows=conn.execute("SELECT s.volunteer_id,s.opportunity_id,s.date,s.time,v.name volunteer_name,o.title,a.status FROM schedules s JOIN volunteers v ON s.volunteer_id=v.id JOIN opportunities o ON s.opportunity_id=o.id LEFT JOIN attendance a ON a.volunteer_id=s.volunteer_id AND a.opportunity_id=s.opportunity_id AND a.date=s.date WHERE o.organization_id=? ORDER BY s.date,s.time",(org["id"],)).fetchall(); conn.close()
    if not rows: return layout("Attendance",'<div class="card empty"><h2>No Attendance Records</h2><p>Schedule volunteers first.</p></div>')
    trs=''.join(f'''<tr><td>{r["volunteer_name"]}</td><td>{r["title"]}</td><td>{r["date"]}</td><td>{r["time"]}</td><td>{r["status"] or "Not Marked"}</td><td><form method="POST" action="/mark-attendance"><input type="hidden" name="volunteer_id" value="{r["volunteer_id"]}"><input type="hidden" name="opportunity_id" value="{r["opportunity_id"]}"><input type="hidden" name="date" value="{r["date"]}"><button name="status" value="Present" class="green">Present</button><button name="status" value="Absent" class="red">Absent</button></form></td></tr>''' for r in rows)
    return layout("Attendance",f'<div class="card"><h2>Attendance Management</h2><p class="small">Attendance is manually selected as Present or Absent.</p><div class="table-wrap"><table><tr><th>Volunteer</th><th>Opportunity</th><th>Date</th><th>Time</th><th>Current Status</th><th>Action</th></tr>{trs}</table></div></div>')


@app.route("/mark-attendance", methods=["POST"])
@role_required("organization")
def mark_attendance():
    vid=request.form.get("volunteer_id"); oid=request.form.get("opportunity_id"); ed=request.form.get("date"); status=request.form.get("status")
    if status not in ("Present","Absent"): flash("Invalid attendance status.","danger"); return redirect(url_for("attendance"))
    conn=get_db_connection(); org=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone(); valid=conn.execute("SELECT s.id FROM schedules s JOIN opportunities o ON s.opportunity_id=o.id WHERE s.volunteer_id=? AND s.opportunity_id=? AND s.date=? AND o.organization_id=?",(vid,oid,ed,org["id"])).fetchone()
    if not valid: conn.close(); flash("Invalid attendance record.","danger"); return redirect(url_for("attendance"))
    existing=conn.execute("SELECT id FROM attendance WHERE volunteer_id=? AND opportunity_id=? AND date=?",(vid,oid,ed)).fetchone()
    if existing: conn.execute("UPDATE attendance SET status=? WHERE id=?",(status,existing["id"]))
    else: conn.execute("INSERT INTO attendance(volunteer_id,opportunity_id,date,status,created_at) VALUES(?,?,?,?,?)",(vid,oid,ed,status,now()))
    conn.commit(); conn.close(); flash(f"Attendance updated to {status}.","success"); return redirect(url_for("attendance"))


@app.route("/completed-events")
@login_required
def completed_events():
    conn=get_db_connection(); cutoff=date.today().isoformat()
    if session["role"]=="organization":
        org=conn.execute("SELECT * FROM organizations WHERE user_id=?",(session["user_id"],)).fetchone(); events=conn.execute("SELECT * FROM opportunities WHERE organization_id=? AND date<? ORDER BY date DESC",(org["id"],cutoff)).fetchall(); cards=''
        for e in events:
            total=conn.execute("SELECT COUNT(*) FROM schedules WHERE opportunity_id=?",(e["id"],)).fetchone()[0]; present=conn.execute("SELECT COUNT(*) FROM attendance WHERE opportunity_id=? AND status='Present'",(e["id"],)).fetchone()[0]; absent=conn.execute("SELECT COUNT(*) FROM attendance WHERE opportunity_id=? AND status='Absent'",(e["id"],)).fetchone()[0]
            cards+=f'<div class="card"><h2>{e["title"]}</h2><p><strong>Date:</strong> {e["date"]}</p><p><strong>Time:</strong> {e["time"]}</p><p><strong>Scheduled:</strong> {total} &nbsp; <strong>Present:</strong> {present} &nbsp; <strong>Absent:</strong> {absent}</p>{badge("Completed")}<br><a class="btn" href="/attendance">View Attendance</a></div>'
    else:
        v=conn.execute("SELECT * FROM volunteers WHERE user_id=?",(session["user_id"],)).fetchone(); events=conn.execute("SELECT s.*,o.title,o.organization,a.status FROM schedules s JOIN opportunities o ON s.opportunity_id=o.id LEFT JOIN attendance a ON a.volunteer_id=s.volunteer_id AND a.opportunity_id=s.opportunity_id AND a.date=s.date WHERE s.volunteer_id=? AND s.date<? ORDER BY s.date DESC",(v["id"],cutoff)).fetchall(); cards=''.join(f'<div class="card"><h2>{e["title"]}</h2><p><strong>Organization:</strong> {e["organization"]}</p><p><strong>Date:</strong> {e["date"]}</p><p><strong>Time:</strong> {e["time"]}</p><p><strong>Attendance:</strong> {e["status"] or "Not Marked"}</p>{badge("Completed")}</div>' for e in events)
    conn.close()
    if not cards: cards='<div class="card empty"><h2>No Completed Events</h2><p>Events automatically appear here after their date has passed.</p></div>'
    return layout("Completed Events",f'<h1>Completed Events</h1>{cards}')


@app.route("/database")
@role_required("organization")
def database_view():
    conn=get_db_connection(); users=conn.execute("SELECT id,role,email,created_at FROM users ORDER BY id").fetchall(); volunteers=conn.execute("SELECT * FROM volunteers ORDER BY id").fetchall(); orgs=conn.execute("SELECT * FROM organizations ORDER BY id").fetchall(); opps=conn.execute("SELECT * FROM opportunities ORDER BY id").fetchall(); schedules_rows=conn.execute("SELECT s.id,v.name volunteer,o.title opportunity,s.date,s.time FROM schedules s JOIN volunteers v ON s.volunteer_id=v.id JOIN opportunities o ON s.opportunity_id=o.id ORDER BY s.id").fetchall(); att=conn.execute("SELECT a.id,v.name volunteer,o.title opportunity,a.date,a.status FROM attendance a JOIN volunteers v ON a.volunteer_id=v.id JOIN opportunities o ON a.opportunity_id=o.id ORDER BY a.id").fetchall(); conn.close()
    def table(headers, rows):
        head=''.join(f'<th>{h}</th>' for h in headers); body=''.join('<tr>'+''.join(f'<td>{r}</td>' for r in row)+ '</tr>' for row in rows); return f'<div class="table-wrap"><table><tr>{head}</tr>{body}</table></div>'
    users_t=table(["ID","Role","Email","Created"],[(r["id"],r["role"],r["email"],r["created_at"]) for r in users]); vol_t=table(["ID","Name","Email","Phone","Skills","Availability"],[(r["id"],r["name"],r["email"],r["phone"],r["skills"],r["availability"]) for r in volunteers]); org_t=table(["ID","Name","Email","Phone","Type","Address"],[(r["id"],r["name"],r["email"],r["phone"],r["organization_type"],r["address"]) for r in orgs]); opp_t=table(["ID","Title","Organization","Skills","Date","Time","Created"],[(r["id"],r["title"],r["organization"],r["required_skills"],r["date"],r["time"],r["created_at"]) for r in opps]); sch_t=table(["ID","Volunteer","Opportunity","Date","Time"],[(r["id"],r["volunteer"],r["opportunity"],r["date"],r["time"]) for r in schedules_rows]); att_t=table(["ID","Volunteer","Opportunity","Date","Status"],[(r["id"],r["volunteer"],r["opportunity"],r["date"],r["status"]) for r in att])
    return layout("Database",f'<h1>Database Records</h1><div class="card"><h2>Users</h2>{users_t}</div><div class="card"><h2>Volunteers</h2>{vol_t}</div><div class="card"><h2>Organizations</h2>{org_t}</div><div class="card"><h2>Opportunities</h2>{opp_t}</div><div class="card"><h2>Schedules</h2>{sch_t}</div><div class="card"><h2>Attendance</h2>{att_t}</div>')


if __name__ == "__main__":
    init_db()
    print("==============================================")
    print("        VolunteerConnect Started")
    print("        http://127.0.0.1:5000")
    print("==============================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
