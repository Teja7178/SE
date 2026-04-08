from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ---------------- USER ----------------
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, default="")
    profile_pic = db.Column(db.String(255), default="default.png")
    is_online = db.Column(db.Boolean, default=False)

    # Relationship with hobbies
    hobbies = db.relationship('UserHobby', backref='user', lazy=True)

# ---------------- HOBBY ----------------
class Hobby(db.Model):
    __tablename__ = 'hobby'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# ---------------- USER-HOBBY ----------------
class UserHobby(db.Model):
    __tablename__ = 'user_hobby'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hobby_id = db.Column(db.Integer, db.ForeignKey('hobby.id'), nullable=False)

    # Relationship to Hobby
    hobby = db.relationship('Hobby')

# ---------------- MATCH ----------------
class Match(db.Model):
    __tablename__ = 'match'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, nullable=False)
    user2_id = db.Column(db.Integer, nullable=False)
    match_score = db.Column(db.Float)
    status = db.Column(db.String(20), default="pending")

# ---------------- MESSAGE ----------------
class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- REPORT ----------------
class Report(db.Model):
    __tablename__ = 'report'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, nullable=False)
    reported_user_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)