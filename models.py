"""
models.py — Database models for Smart Agriculture AI.

Tables:
  User     — farmers, admins, government users
  Analysis — crop analysis results linked to users
  ChatLog  — conversation history per analysis
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20),  nullable=False, default="farmer")
    # role: "farmer" | "admin" | "government"

    # Farmer profile
    full_name     = db.Column(db.String(120), nullable=True)
    phone         = db.Column(db.String(30),  nullable=True)
    province      = db.Column(db.String(60),  nullable=True)
    commune       = db.Column(db.String(60),  nullable=True)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime, nullable=True)
    is_active     = db.Column(db.Boolean, default=True)

    # Relationships
    analyses      = db.relationship("Analysis", backref="user", lazy=True,
                                    cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_government(self) -> bool:
        return self.role == "government"

    @property
    def is_farmer(self) -> bool:
        return self.role == "farmer"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Analysis(db.Model):
    __tablename__ = "analyses"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # nullable=True so anonymous uploads still get saved for dataset

    # Image info
    filename       = db.Column(db.String(200), nullable=False)

    # AI result
    crop_type      = db.Column(db.String(80),  nullable=True)
    growth_stage   = db.Column(db.String(80),  nullable=True)
    health_score   = db.Column(db.Float,       nullable=True)
    overall_status = db.Column(db.String(20),  nullable=True)
    summary        = db.Column(db.Text,        nullable=True)
    detections     = db.Column(db.Text,        nullable=True)  # JSON string
    recommendations= db.Column(db.Text,        nullable=True)  # JSON string
    had_error      = db.Column(db.Boolean,     default=False)

    # Dataset fields — for national statistics
    province       = db.Column(db.String(60),  nullable=True)
    commune        = db.Column(db.String(60),  nullable=True)
    season         = db.Column(db.String(20),  nullable=True)  # "A" or "B"
    latitude       = db.Column(db.Float,       nullable=True)
    longitude      = db.Column(db.Float,       nullable=True)

    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    chat_logs      = db.relationship("ChatLog", backref="analysis", lazy=True,
                                     cascade="all, delete-orphan")

    @property
    def detections_list(self) -> list:
        import json
        try:
            return json.loads(self.detections or "[]")
        except Exception:
            return []

    @property
    def recommendations_list(self) -> list:
        import json
        try:
            return json.loads(self.recommendations or "[]")
        except Exception:
            return []

    def __repr__(self):
        return f"<Analysis {self.id} {self.crop_type} {self.overall_status}>"


class ChatLog(db.Model):
    __tablename__ = "chat_logs"

    id          = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analyses.id"), nullable=False)
    role        = db.Column(db.String(10), nullable=False)   # "user" or "model"
    content     = db.Column(db.Text,       nullable=False)
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatLog {self.analysis_id} {self.role}>"
