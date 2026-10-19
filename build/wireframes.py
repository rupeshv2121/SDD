"""Illustrative wireframes for authenticated pages, built from the labels,
fields and navigation found in CampusCure_Frontend/src. Writes HTML files to
build/wf/; shoot_wireframes.cjs renders them to ../images/wf-*.png.

They are schematic on purpose (greyscale, no real data) and every one is
stamped ILLUSTRATIVE WIREFRAME so nobody mistakes it for a screenshot.
"""
import html
import pathlib

OUT = pathlib.Path(__file__).parent / "wf"
OUT.mkdir(exist_ok=True)

NAV = {
    "student": [("Overview", ["Dashboard"]), ("Complaints", ["Raise Complaint", "My Complaints"]),
                ("Learning", ["Doubt Community", "Saved Doubts", "Reputation", "Staff Directory"])],
    "faculty": [("Overview", ["Dashboard"]),
                ("Workload", ["Complaints", "Doubts", "Reputation", "My Performance", "Staff Directory"])],
    "admin": [("Overview", ["Dashboard"]), ("Operations", ["Complaints", "Users", "Faculty Performance", "Staff Directory"])],
    "superadmin": [("Overview", ["Dashboard"]),
                   ("Operations", ["All Complaints", "Escalated", "Users", "Faculty Performance", "Staff Directory"]),
                   ("System", ["Settings"])],
}
ROLE_LABEL = {"student": "Student", "faculty": "Faculty", "admin": "Admin", "superadmin": "Super Admin"}

CSS = """
*{box-sizing:border-box} body{margin:0;font:13px/1.45 Arial,Helvetica,sans-serif;color:#222;background:#fff}
.shell{display:grid;grid-template-columns:210px 1fr;width:1280px;min-height:780px;border:2px solid #333}
.side{background:#f1f1f1;border-right:1.5px solid #555;padding:14px 12px}
.brand{font-weight:bold;font-size:16px;margin-bottom:16px}.brand span{display:inline-block;width:18px;height:18px;border:2px solid #333;border-radius:4px;vertical-align:-3px;margin-right:6px}
.grp{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#666;margin:12px 0 4px}
.nav{padding:6px 8px;border-radius:4px;margin-bottom:2px}.nav.on{background:#d9d9d9;font-weight:bold;border-left:3px solid #333}
.main{display:flex;flex-direction:column}
.top{height:52px;border-bottom:1.5px solid #555;display:flex;align-items:center;justify-content:space-between;padding:0 18px}
.top .r{display:flex;gap:10px;align-items:center}.ic{width:26px;height:26px;border:1.5px solid #555;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px}
.content{padding:18px 22px;display:flex;flex-direction:column;gap:14px;position:relative;flex:1}
h1{font-size:20px;margin:0}.sub{color:#555;margin-top:2px}
.row{display:flex;gap:12px;flex-wrap:wrap}.col{display:flex;flex-direction:column;gap:10px}
.box{border:1.5px solid #555;border-radius:6px;padding:12px;background:#fff}
.stat{flex:1;min-width:150px}.stat b{display:block;font-size:22px}.muted{color:#666}
.btn{display:inline-block;border:1.5px solid #333;border-radius:5px;padding:6px 12px;background:#e6e6e6;font-weight:bold}
.btn.p{background:#333;color:#fff}.btn.o{background:#fff}
.inp{border:1.5px solid #777;border-radius:4px;padding:7px 9px;color:#777;background:#fafafa}
.lbl{font-weight:bold;font-size:12px;margin-bottom:3px}
.chip{display:inline-block;border:1px solid #666;border-radius:10px;padding:1px 8px;font-size:11px;margin-right:4px;background:#f3f3f3}
.badge{display:inline-block;border:1.5px solid #333;border-radius:3px;padding:1px 6px;font-size:10px;font-weight:bold;letter-spacing:.04em}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #888;padding:7px 8px;text-align:left}th{background:#e9e9e9}
.line{height:9px;background:#d6d6d6;border-radius:3px;margin:6px 0}.line.s{width:55%}.line.m{width:78%}
.chart{height:150px;border:1.5px dashed #777;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#666;background:repeating-linear-gradient(45deg,#fafafa,#fafafa 8px,#f0f0f0 8px,#f0f0f0 16px)}
.img{height:70px;width:100px;border:1.5px solid #777;background:linear-gradient(135deg,#eee 49%,#999 50%,#eee 51%)}
.modal{position:absolute;inset:0;background:rgba(0,0,0,.28);display:flex;align-items:flex-start;justify-content:center;padding-top:30px}
.modal .box{width:560px;box-shadow:0 4px 0 #555}
.stamp{position:absolute;right:14px;bottom:10px;border:2px dashed #b00;color:#b00;font-weight:bold;padding:4px 10px;font-size:12px;letter-spacing:.06em;background:#fff}
.tabs{display:flex;gap:0;border-bottom:1.5px solid #555}.tab{padding:6px 14px;border:1.5px solid #555;border-bottom:none;margin-right:-1.5px;background:#f3f3f3}.tab.on{background:#fff;font-weight:bold}
.chat{position:absolute;right:22px;bottom:46px;width:340px;border:2px solid #333;border-radius:8px;background:#fff;box-shadow:0 4px 0 #555}
.chat .h{background:#333;color:#fff;padding:8px 10px;font-weight:bold;border-radius:6px 6px 0 0}
.msg{margin:8px 10px;padding:7px 9px;border-radius:6px;border:1px solid #888;max-width:80%}.msg.u{margin-left:auto;background:#e6e6e6}
.fab{position:absolute;right:22px;bottom:12px}
.draft{border:2px dashed #333;background:#f7f7f7}
"""


def e(s):
    return html.escape(s)


def page(name, role, active, body, overlay=""):
    nav = ""
    for grp, items in NAV[role]:
        nav += f'<div class="grp">{e(grp)}</div>'
        for it in items:
            nav += f'<div class="nav{" on" if it == active else ""}">{e(it)}</div>'
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="shell"><aside class="side"><div class="brand"><span></span>CampusCure</div>{nav}</aside>
<div class="main"><div class="top"><div class="muted">{e(ROLE_LABEL[role])} workspace</div>
<div class="r"><span class="chip">EN / हिंदी</span><span class="ic">🔔</span><span class="ic">◐</span><span class="ic">A</span></div></div>
<div class="content">{body}{overlay}<div class="stamp">ILLUSTRATIVE WIREFRAME — NOT A SCREENSHOT</div></div></div></div></body></html>"""
    (OUT / f"wf-{name}.html").write_text(doc, encoding="utf-8")


def header(title, sub, right=""):
    return f'<div class="row" style="justify-content:space-between;align-items:flex-end"><div><h1>{e(title)}</h1><div class="sub">{e(sub)}</div></div><div>{right}</div></div>'


def stats(items):
    return '<div class="row">' + "".join(f'<div class="box stat"><span class="muted">{e(a)}</span><b>{e(b)}</b></div>' for a, b in items) + "</div>"


def field(label, ph, w="100%"):
    return f'<div style="width:{w}"><div class="lbl">{e(label)}</div><div class="inp">{e(ph)}</div></div>'


def table(cols, rows):
    h = "".join(f"<th>{e(c)}</th>" for c in cols)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{h}</tr>{b}</table>"


L = '<div class="line m"></div>'
LS = '<div class="line s"></div>'

# 1 Student dashboard
page("student-dashboard", "student", "Dashboard",
     header("Welcome back, Student", "Your complaints and doubts at a glance") +
     stats([("Total complaints", "n"), ("Active complaints", "n"), ("Doubts asked", "n"), ("Resolution Rate", "n %")]) +
     '<div class="row"><div class="box" style="flex:2"><div class="lbl">Quick Actions</div><span class="btn p">Raise Complaint</span> <span class="btn">Ask a Doubt</span> <span class="btn o">Staff Directory</span></div></div>'
     '<div class="row"><div class="box" style="flex:1"><div class="lbl">Recent complaints</div>' + (L + LS + '<span class="badge">IN_PROGRESS</span>') * 2 +
     '</div><div class="box" style="flex:1"><div class="lbl">Recent doubts</div>' + (L + LS + '<span class="badge">ANSWERED</span>') * 2 + "</div></div>",
     '<div class="fab"><span class="btn p">Assistant</span></div>')

# 2 Doubt community + 3 Ask modal
community_body = (header("Doubt Community", "Ask, answer, and learn together", '<span class="btn p">Ask a Doubt</span>') +
    '<div class="row">' + field("Search", "Search doubts...", "40%") + field("Subject", "Filter by subject", "22%") + field("Semester", "Semester", "14%") + "</div>"
    '<div class="tabs"><div class="tab on">All</div><div class="tab">My doubts</div><div class="tab">Unanswered</div></div>'
    '<div class="row"><div class="col" style="flex:3">' +
    ('<div class="box"><div class="row" style="justify-content:space-between"><b>Doubt title</b><span class="badge">OPEN</span></div>' + L +
     '<span class="chip">dbms</span><span class="chip">indexing</span> <span class="muted">▲ n · n answers · n views · Subject · Sem n</span></div>') * 3 +
    '</div><div class="box" style="flex:1.2"><div class="lbl">Most Active Subjectwise Doubts</div><div class="chart" style="height:180px">bar chart</div></div></div>')
page("doubt-community", "student", "Doubt Community", community_body, '<div class="fab"><span class="btn p">Assistant</span></div>')
page("ask-doubt", "student", "Doubt Community", community_body,
     '<div class="modal"><div class="box col"><b style="font-size:16px">Ask a Doubt</b>' +
     field("Title", "What's your question?") +
     '<div><div class="lbl">Description</div><div class="inp" style="height:90px">B  I  Code  Math  Link  Image | rich-text editor (TipTap)</div></div>'
     '<div class="row">' + field("Subject", "Select Subject", "48%") + field("Semester", "Semester", "48%") + "</div>" +
     field("Labels (comma-separated)", "tag input, max 5") +
     '<div><div class="lbl">Screenshots or notes (optional)</div><div class="inp">Drop files: JPEG, PNG, WebP, HEIC, PDF up to 5 MB</div><div style="margin-top:4px"><span class="btn">Read my question from the image</span> <span class="muted">Works on JPG, PNG and WebP photos of a written question.</span></div></div>'
     '<div class="box draft"><div class="lbl">Similar doubts found</div>' + LS + LS + '</div>'
     '<div style="text-align:right"><span class="btn o">Cancel</span> <span class="btn p">Post Doubt</span></div></div></div>')

# 4 Doubt detail
page("doubt-detail", "student", "Doubt Community",
     '<div class="box"><div class="row" style="justify-content:space-between"><b style="font-size:17px">Doubt title</b><span><span class="badge">ANSWERED</span> <span class="btn o">▲ n</span> <span class="btn o">☆ Save</span></span></div>' + L + L + LS +
     '<span class="chip">tag</span><span class="chip">tag</span> <span class="muted">Edited n times · attachment.pdf</span></div>'
     '<div class="lbl">Answers</div>' +
     '<div class="box"><b>Faculty name</b> <span class="badge">FACULTY</span> <span class="badge">VERIFIED</span> <span class="badge">ACCEPTED</span>' + L + LS + '<div class="muted">▲ Upvote this answer</div></div>'
     '<div class="box"><b>Student name</b>' + L + '<span class="btn o">✓ Accept</span> <span class="btn o">▲</span></div>'
     '<div class="box"><div class="lbl">Your Answer</div><div class="inp" style="height:80px">Write your answer here… (rich-text editor)</div><div style="text-align:right;margin-top:6px"><span class="btn p">Post Answer</span></div></div>')

# 5 Raise complaint
page("raise-complaint", "student", "Raise Complaint",
     header("Raise a Complaint", "Report classroom or facility issues to the administration") +
     '<div class="box col"><div class="lbl">Describe the problem</div><div class="inp" style="height:60px">What is wrong, and where?</div><div><span class="btn">Fill the form for me</span></div></div>'
     '<div class="box draft"><b>A similar complaint has already been reported for this room</b><div class="muted">If your problem is different, please carry on and submit — this is only a suggestion.</div></div>'
     '<div class="row"><div class="box col" style="flex:1"><div class="lbl">Classification</div>' + field("Category", "Select category") + field("Priority", "Select priority (1–5)") +
     '</div><div class="box col" style="flex:1"><div class="lbl">Location</div>' + field("Block", "Select block") + field("Classroom", "Select block first") + "</div></div>"
     '<div class="box col"><div class="lbl">Details</div>' + field("Title", "Short title") + field("Description", "Describe the issue") +
     '<div class="inp">Photos (optional) — location metadata stripped before upload</div></div><div style="text-align:right"><span class="btn p">Submit Complaint</span></div>')

# 6 My complaints
page("my-complaints", "student", "My Complaints",
     header("My Complaints", "Track the status of every issue you have reported") +
     '<div class="row">' + field("Search", "Search by title...", "45%") + field("Status", "All statuses", "25%") + "</div>"
     '<div class="box"><div class="row" style="justify-content:space-between"><b>Complaint title</b><span class="badge">PENDING_CONFIRMATION</span></div>'
     '<div class="muted">Block · Room · Category · Assigned to: staff name · Submitted / Updated</div><div class="lbl" style="margin-top:8px">Resolution note</div>' + L +
     '<div class="row"><div><div class="muted">Before</div><div class="img"></div></div><div><div class="muted">After</div><div class="img"></div></div></div>'
     '<div style="margin-top:8px"><span class="btn p">✓ Yes, Issue Fixed</span> <span class="btn o">✗ Not Fixed</span></div></div>'
     '<div class="box"><div class="row" style="justify-content:space-between"><b>Complaint title</b><span class="badge">RESOLVED</span></div>' + LS +
     '<div class="lbl">Rate Resolution</div>☆ ☆ ☆ ☆ ☆ <div class="inp" style="margin-top:4px">Comment (optional)</div><div style="margin-top:6px"><span class="btn">Submit Feedback</span></div></div>')

# 7 Faculty doubt detail with AI draft
page("faculty-doubt-detail", "faculty", "Doubts",
     '<div class="box"><b style="font-size:17px">Doubt title</b><span class="badge" style="margin-left:8px">OPEN</span>' + L + LS + "</div>"
     '<div class="box draft"><b>🤖 AI-drafted answer</b> <span class="muted">— Written from n previously approved answers · Not visible to students</span>'
     '<div class="inp" style="height:80px;margin-top:6px">Editable draft text…</div><div class="muted">▸ Show sources</div>'
     '<div style="text-align:right"><span class="btn o">Reject</span> <span class="btn p">Approve and publish</span></div></div>'
     '<div class="lbl">Answers</div><div class="box"><b>Student name</b> <span class="badge">PENDING</span> <span class="muted">Not visible to students</span>' + L +
     '<span class="btn o">Moderate</span></div><div class="box"><div class="lbl">Your Answer</div><div class="inp" style="height:60px">Write your answer here (minimum 10 characters)...</div></div>')

# 8 Faculty assigned complaints
page("faculty-complaints", "faculty", "Complaints",
     header("Assigned Complaints", "Issues routed to you, newest first") +
     table(["Title", "Room", "Category", "Status", "Timeline", "Action"],
           [["Complaint title", "Block / Room", "FAN", '<span class="badge">ASSIGNED</span>', "Assigned · due", '<span class="btn">Update Status</span>'],
            ["Complaint title", "Block / Room", "NETWORK", '<span class="badge">IN_PROGRESS</span>', "Assigned · due", '<span class="btn">Update Status</span>']]),
     '<div class="modal"><div class="box col" style="width:480px"><b>Update Status</b>' + field("Status", "IN_PROGRESS / PENDING_CONFIRMATION") +
     field("Resolution note", "What was done") + '<div class="inp">Repair photo (optional)</div><div style="text-align:right"><span class="btn p">Update</span></div></div></div>')

# 9 Admin complaints with assignment candidates
page("admin-complaints", "admin", "Complaints",
     header("Complaint Management", "n complaints") +
     '<div class="box draft"><b>Possible duplicates</b> <span class="muted">n groups of open complaints that look like the same fault</span></div>'
     '<div class="row">' + field("Search", "Search complaints...", "40%") + field("Status", "All", "20%") + "</div>" +
     table(["Title", "Category", "Location", "Priority", "Status", "Assigned to", "Actions"],
           [["Complaint title", "LIGHT", "Block / Room", "4", '<span class="badge">RAISED</span>', "—", '<span class="btn">Assign</span> <span class="btn o">Status</span>']] * 3),
     '<div class="modal"><div class="box col" style="width:560px"><b>Assign Faculty</b><div class="muted">Ranked suggestions — the Admin decides</div>' +
     table(["Candidate", "Match reason", "Open load"], [["Staff name", "Handles this category, same department", "n"], ["Staff name", "Handles this category", "n"], ["Staff name", "Non-teaching, general", "n"]]) +
     '<div style="text-align:right"><span class="btn o">Cancel</span> <span class="btn p">Assign</span></div></div></div>')

# 10 Admin users
page("admin-users", "admin", "Users",
     header("User Management", "n users") + '<div class="row">' + field("Search", "Search users...", "40%") + field("Role", "All roles", "20%") + "</div>" +
     table(["Name", "Email", "Role", "Approval", "Active", "Created", "Actions"],
           [["User name", "user@…", "STUDENT", '<span class="badge">PENDING</span>', "off", "date", '<span class="btn">Approval</span> <span class="btn o">Details</span>']] * 4),
     '<div class="modal"><div class="box col" style="width:440px"><b>Change Approval Status</b>' + field("New Approval Status", "APPROVED / REJECTED / PENDING") +
     '<div><div class="lbl">Account Active</div><div class="muted">Enable or disable this user\'s access</div></div><div style="text-align:right"><span class="btn p">Save</span></div></div></div>')

# 11 Super admin escalations
page("superadmin-escalated", "superadmin", "Escalated",
     header("Escalated Complaints", "n complaints need review") + field("Search", "Search by title or reason...", "40%") +
     '<div class="box"><div class="row" style="justify-content:space-between"><b>Complaint title</b><span class="badge">SUPERADMIN REVIEW REQUIRED</span></div>'
     '<div class="muted">Raised By · Current Assignment · escalation count n</div><div class="lbl" style="margin-top:6px">Student\'s Rejection Reason</div>' + L +
     '<div class="lbl">Previous Resolution Attempt</div>' + LS + '<div class="lbl">Assignment History</div>' + LS + LS +
     '<div style="text-align:right"><span class="btn p">Reassign</span></div></div>',
     '<div class="modal"><div class="box col" style="width:480px"><b>Reassign Escalated Complaint</b>' + field("Select Faculty Member", "Select Faculty") +
     field("SuperAdmin Notes (Optional)", "Instructions for the new assignee") + '<div style="text-align:right"><span class="btn p">Reassign</span></div></div></div>')

# 12 Profile and security
page("profile-security", "student", "",
     header("My Profile", "Personal information and security") +
     '<div class="row"><div class="box col" style="flex:1"><div class="lbl">Personal Information</div>' + field("Display Name", "Name") + field("Phone Number", "Phone") + field("Address", "Address") +
     '</div><div class="box col" style="flex:1"><div class="lbl">Academic Information</div>' + field("Department", "Department") + field("Semester", "n") +
     '<div class="lbl">Guardian Details</div>' + field("Guardian Name", "Name") + "</div></div>"
     '<div class="row"><div class="box" style="flex:1"><div class="lbl">Two-step verification</div>' + LS + '<span class="btn">Set up</span></div>'
     '<div class="box" style="flex:1"><div class="lbl">Browser notifications</div>' + LS + '<span class="btn">Turn on</span></div>'
     '<div class="box" style="flex:1"><div class="lbl">Telegram</div>' + LS + '<span class="btn">Connect Telegram</span></div></div>')

# 13 Assistant widget over dashboard
page("assistant", "student", "Dashboard",
     header("Welcome back, Student", "Your complaints and doubts at a glance") + stats([("Total complaints", "n"), ("Active", "n"), ("Doubts asked", "n")]),
     '<div class="chat"><div class="h">CampusCure Assistant · AI</div>'
     '<div class="msg u">What is happening with my Wi-Fi complaint?</div>'
     '<div class="msg">Your complaint is IN_PROGRESS and assigned to … (from getMyComplaints)</div>'
     '<div class="msg u">Has anyone asked about B-trees?</div><div class="msg">Similar doubts: … (from searchDoubts)</div>'
     '<div style="padding:8px 10px;border-top:1px solid #888"><div class="inp">Ask about your complaints or doubts…</div></div></div>')

# 14 Admin dashboard
page("admin-dashboard", "admin", "Dashboard",
     header("Admin Dashboard", "Campus-wide complaints, doubts and users") +
     stats([("Total complaints", "n"), ("Pending", "n"), ("Resolved", "n"), ("Users", "n")]) +
     '<div class="row"><div class="box" style="flex:2"><div class="lbl">Monthly Trends</div><div class="chart">area chart</div></div>'
     '<div class="box" style="flex:1"><div class="lbl">By Category</div><div class="chart">pie chart</div></div></div>'
     '<div class="row"><div class="box" style="flex:1"><div class="lbl">By Department</div><div class="chart">bar chart</div></div></div>')

print("wireframes:", len(list(OUT.glob("*.html"))))
