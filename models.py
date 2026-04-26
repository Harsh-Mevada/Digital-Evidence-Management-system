from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))


class Case(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    case_name = db.Column(db.String(200))
    description = db.Column(db.Text)


class Evidence(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(200))
    file_path = db.Column(db.String(300))
    hash_value = db.Column(db.String(200))
    case_id = db.Column(db.Integer)
    status = db.Column(db.String(50))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)


class CustodyLog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    evidence_id = db.Column(db.Integer)
    action = db.Column(db.String(100))
    user = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime)