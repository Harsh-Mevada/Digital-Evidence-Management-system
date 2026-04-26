from flask import Flask, render_template, request, redirect, session, send_file
import config
import os
import hashlib
from datetime import datetime

from models import db, User, Evidence, Case, CustodyLog

app = Flask(__name__)
app.config.from_object(config)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

UPLOAD_FOLDER = config.UPLOAD_FOLDER

# create uploads folder automatically
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {"png","jpg","jpeg","mp4","pdf","docx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email,password=password).first()

        if user:
            session["user"] = user.email
            return redirect("/dashboard")

        else:
            return "Invalid login"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    evidence_count = Evidence.query.count()
    case_count = Case.query.count()

    return render_template(
        "dashboard.html",
        evidence_count=evidence_count,
        case_count=case_count
    )


@app.route("/upload", methods=["GET","POST"])
def upload():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        file = request.files["file"]

        if file.filename == "":
            return "No file selected"

        if not allowed_file(file.filename):
            return "File type not allowed"

        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        file.save(filepath)

        with open(filepath,"rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        evidence = Evidence(
            file_name=filename,
            file_path=filepath,
            hash_value=file_hash,
            status="UPLOADED"
        )

        db.session.add(evidence)
        db.session.commit()

        log = CustodyLog(
            evidence_id=evidence.id,
            action="UPLOAD",
            user=session.get("user"),
            timestamp=datetime.now()
        )

        db.session.add(log)
        db.session.commit()

        return redirect("/evidence")

    return render_template("upload.html")


@app.route("/evidence")
def evidence():

    evidences = Evidence.query.all()

    return render_template(
        "evidence_list.html",
        evidences=evidences
    )


@app.route("/download/<int:id>")
def download(id):

    evidence = Evidence.query.get(id)

    log = CustodyLog(
        evidence_id=evidence.id,
        action="DOWNLOAD",
        user=session.get("user"),
        timestamp=datetime.now()
    )

    db.session.add(log)
    db.session.commit()

    return send_file(evidence.file_path, as_attachment=True)

@app.route("/delete/<int:id>")
def delete(id):

    evidence = Evidence.query.get(id)

    if not evidence:
        return "Evidence not found"

    # delete file from uploads folder
    if os.path.exists(evidence.file_path):
        os.remove(evidence.file_path)

    # log deletion
    log = CustodyLog(
        evidence_id=evidence.id,
        action="DELETE",
        user=session.get("user"),
        timestamp=datetime.now()
    )

    db.session.add(log)

    # delete from database
    db.session.delete(evidence)
    db.session.commit()

    return redirect("/evidence")


@app.route("/logs")
def logs():

    logs = CustodyLog.query.all()

    return render_template("logs.html", logs=logs)

@app.route("/cases", methods=["GET","POST"])
def cases():

    if request.method == "POST":

        name = request.form["name"]
        desc = request.form["description"]

        case = Case(case_name=name,description=desc)

        db.session.add(case)
        db.session.commit()

    cases = Case.query.all()

    return render_template("cases.html", cases=cases)

@app.route("/verify")
def verify():

    evidences = Evidence.query.all()

    results = []

    for e in evidences:

        try:
            with open(e.file_path,"rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()

            if current_hash == e.hash_value:
                status = "SAFE"
            else:
                status = "TAMPERED"

        except:
            status = "FILE MISSING"

        results.append({
            "id": e.id,
            "name": e.file_name,
            "stored_hash": e.hash_value,
            "current_hash": current_hash if 'current_hash' in locals() else "N/A",
            "status": status
        })

    return render_template("verify.html", results=results)

@app.route("/report")
def report():

    evidences = Evidence.query.all()

    return render_template("report.html", evidences=evidences)


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)
