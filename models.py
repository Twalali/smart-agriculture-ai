"""
models.py — Smart Agriculture AI database models.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20),  nullable=False, default="farmer")
    language      = db.Column(db.String(5),   nullable=False, default="fr")  # fr | rn | en
    theme         = db.Column(db.String(10),  nullable=False, default="dark") # dark | light

    full_name     = db.Column(db.String(120), nullable=True)
    phone         = db.Column(db.String(30),  nullable=True)
    province      = db.Column(db.String(60),  nullable=True)
    commune       = db.Column(db.String(60),  nullable=True)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime, nullable=True)
    is_active                = db.Column(db.Boolean, default=True)
    is_verified_professional = db.Column(db.Boolean, default=False)

    analyses      = db.relationship("Analysis", backref="user", lazy=True, cascade="all, delete-orphan")
    farms         = db.relationship("Farm", backref="owner", lazy=True, cascade="all, delete-orphan")
    forum_posts   = db.relationship("ForumPost", backref="author", lazy=True, cascade="all, delete-orphan")
    forum_replies = db.relationship("ForumReply", backref="author", lazy=True, cascade="all, delete-orphan")
    sent_messages = db.relationship("DirectMessage", foreign_keys="DirectMessage.sender_id", backref="sender", lazy=True, cascade="all, delete-orphan")
    recv_messages = db.relationship("DirectMessage", foreign_keys="DirectMessage.receiver_id", backref="receiver", lazy=True)

    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

    @property
    def is_admin(self): return self.role == "admin"
    @property
    def is_government(self): return self.role in ("admin", "government")
    @property
    def is_farmer(self): return self.role == "farmer"
    def __repr__(self): return f"<User {self.username}>"


class Analysis(db.Model):
    __tablename__ = "analyses"
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    filename       = db.Column(db.String(200), nullable=False)
    crop_type      = db.Column(db.String(80),  nullable=True)
    growth_stage   = db.Column(db.String(80),  nullable=True)
    health_score   = db.Column(db.Float,       nullable=True)
    overall_status = db.Column(db.String(20),  nullable=True)
    summary        = db.Column(db.Text,        nullable=True)
    detections     = db.Column(db.Text,        nullable=True)
    recommendations= db.Column(db.Text,        nullable=True)
    had_error      = db.Column(db.Boolean,     default=False)
    province       = db.Column(db.String(60),  nullable=True)
    commune        = db.Column(db.String(60),  nullable=True)
    season         = db.Column(db.String(20),  nullable=True)
    latitude       = db.Column(db.Float,       nullable=True)
    longitude      = db.Column(db.Float,       nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    chat_logs      = db.relationship("ChatLog", backref="analysis", lazy=True, cascade="all, delete-orphan")

    @property
    def detections_list(self):
        try: return json.loads(self.detections or "[]")
        except: return []

    @property
    def recommendations_list(self):
        try: return json.loads(self.recommendations or "[]")
        except: return []


class ChatLog(db.Model):
    __tablename__ = "chat_logs"
    id          = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analyses.id"), nullable=False)
    role        = db.Column(db.String(10), nullable=False)
    content     = db.Column(db.Text,       nullable=False)
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow)


class Farm(db.Model):
    __tablename__ = "farms"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name        = db.Column(db.String(120), nullable=False)
    province    = db.Column(db.String(60),  nullable=True)
    commune     = db.Column(db.String(60),  nullable=True)
    description = db.Column(db.Text,        nullable=True)
    latitude    = db.Column(db.Float,       nullable=True)
    longitude   = db.Column(db.Float,       nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    fields      = db.relationship("Field", backref="farm", lazy=True, cascade="all, delete-orphan")

    @property
    def total_area_ha(self): return sum(f.area_ha or 0 for f in self.fields)
    @property
    def total_fields(self): return len(self.fields)


class Field(db.Model):
    __tablename__ = "fields"
    id              = db.Column(db.Integer, primary_key=True)
    farm_id         = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    name            = db.Column(db.String(120), nullable=False, default="Field")
    crop            = db.Column(db.String(80),  nullable=True)
    season          = db.Column(db.String(10),  nullable=True)  # A | B | C
    location_method = db.Column(db.String(20),  nullable=True, default="draw")
    length_m        = db.Column(db.Float, nullable=True)
    width_m         = db.Column(db.Float, nullable=True)
    geojson         = db.Column(db.Text,  nullable=True)
    area_m2         = db.Column(db.Float, nullable=True)
    area_ha         = db.Column(db.Float, nullable=True)
    center_lat      = db.Column(db.Float, nullable=True)
    center_lng      = db.Column(db.Float, nullable=True)
    seed_required   = db.Column(db.Float, nullable=True)
    fertilizer_npk  = db.Column(db.Float, nullable=True)
    fertilizer_urea = db.Column(db.Float, nullable=True)
    plant_population= db.Column(db.Integer, nullable=True)
    expected_yield  = db.Column(db.Float, nullable=True)
    expected_revenue= db.Column(db.Float, nullable=True)
    market_price    = db.Column(db.Float, nullable=True)
    risk_level      = db.Column(db.String(20), nullable=True)
    notes           = db.Column(db.Text, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def geojson_dict(self):
        try: return json.loads(self.geojson or "{}")
        except: return {}


class CropRequirements(db.Model):
    __tablename__ = "crop_requirements"
    id                  = db.Column(db.Integer, primary_key=True)
    crop_name           = db.Column(db.String(80), unique=True, nullable=False)
    local_name          = db.Column(db.String(80), nullable=True)
    seed_rate_kg_ha     = db.Column(db.Float, nullable=False)
    npk_rate_kg_ha      = db.Column(db.Float, nullable=False)
    urea_rate_kg_ha     = db.Column(db.Float, nullable=False)
    row_spacing_cm      = db.Column(db.Float, nullable=False)
    plant_spacing_cm    = db.Column(db.Float, nullable=False)
    yield_ton_ha        = db.Column(db.Float, nullable=False)
    market_price_bif_kg = db.Column(db.Float, nullable=True)
    planting_depth_cm   = db.Column(db.Float, nullable=True)
    days_to_harvest     = db.Column(db.Integer, nullable=True)
    best_season         = db.Column(db.String(40), nullable=True)
    notes               = db.Column(db.Text, nullable=True)


class ForumPost(db.Model):
    __tablename__ = "forum_posts"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    crop_tag   = db.Column(db.String(80), nullable=True)
    category   = db.Column(db.String(40), nullable=True, default="general")
    is_pinned  = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    replies    = db.relationship("ForumReply", backref="post", lazy=True,
                                  cascade="all, delete-orphan", order_by="ForumReply.created_at")

    @property
    def reply_count(self): return len(self.replies)

    @property
    def last_activity(self):
        if self.replies: return self.replies[-1].created_at
        return self.created_at


class ForumReply(db.Model):
    __tablename__ = "forum_replies"
    id         = db.Column(db.Integer, primary_key=True)
    post_id    = db.Column(db.Integer, db.ForeignKey("forum_posts.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    is_solution= db.Column(db.Boolean, default=False)  # marked as answer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DirectMessage(db.Model):
    __tablename__ = "direct_messages"
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body        = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type       = db.Column(db.String(40), nullable=False)  # disease_alert|forum_reply|announcement|market
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=True)
    link       = db.Column(db.String(200), nullable=True)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("notifications",
                           lazy=True, cascade="all, delete-orphan"))


class MarketPrice(db.Model):
    __tablename__ = "market_prices"
    id         = db.Column(db.Integer, primary_key=True)
    crop_name  = db.Column(db.String(80),  nullable=False)
    local_name = db.Column(db.String(80),  nullable=True)
    price_bif  = db.Column(db.Float,       nullable=False)  # BIF per kg
    province   = db.Column(db.String(60),  nullable=False)
    market     = db.Column(db.String(120), nullable=True)   # market name e.g. "Marché de Gitega"
    posted_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    notes      = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    poster = db.relationship("User", backref=db.backref("market_prices", lazy=True))
