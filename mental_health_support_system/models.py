"""
models.py — SQLAlchemy Database Models
========================================
Defines all ORM models that map to MySQL tables.
Each class = one table. Relationships are declared
using SQLAlchemy's relationship() helper.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# db instance — imported into app.py and all route files
db = SQLAlchemy()


# ======================================================================
# ADMIN MODEL
# ======================================================================
class Admin(db.Model, UserMixin):
    """Platform administrator. Can manage all content and users."""
    __tablename__ = 'admins'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    # Tell Flask-Login this is an admin
    def get_id(self):
        return f"admin-{self.id}"

    def __repr__(self):
        return f'<Admin {self.username}>'


# ======================================================================
# USER MODEL
# ======================================================================
class User(db.Model, UserMixin):
    """
    Registered patient / general user.
    Also used as the base account for therapists
    (a therapist has a User record + a Therapist profile).
    """
    __tablename__ = 'users'

    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(80),  unique=True, nullable=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    password        = db.Column(db.String(255), nullable=False)
    full_name       = db.Column(db.String(150))
    phone           = db.Column(db.String(20))
    date_of_birth   = db.Column(db.Date)
    gender          = db.Column(db.Enum('male','female','other','prefer_not_to_say'))
    profile_picture = db.Column(db.String(255), default='default.png')
    bio             = db.Column(db.Text)
    is_active       = db.Column(db.Boolean, default=True)
    role            = db.Column(db.String(20), default='user')   # 'user' or 'therapist'
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    # ---- Relationships ----
    therapist_profile = db.relationship('Therapist', backref='user',
                                        uselist=False, lazy=True)
    appointments      = db.relationship('Appointment', foreign_keys='Appointment.user_id',
                                        backref='patient', lazy=True)
    mood_logs         = db.relationship('MoodLog',     backref='user', lazy=True)
    journal_entries   = db.relationship('JournalEntry',backref='user', lazy=True)
    sent_messages     = db.relationship('Message', foreign_keys='Message.sender_id',
                                        backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id',
                                        backref='receiver', lazy=True)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'


# ======================================================================
# THERAPIST MODEL
# ======================================================================
class Therapist(db.Model):
    """
    Extended profile for therapists.
    One-to-one with User (role='therapist').
    Must be approved by admin before appearing in listings.
    """
    __tablename__ = 'therapists'

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'),
                                 nullable=False, unique=True)
    specialization   = db.Column(db.String(150))
    license_number   = db.Column(db.String(100))
    years_experience = db.Column(db.Integer, default=0)
    education        = db.Column(db.Text)
    bio              = db.Column(db.Text)
    consultation_fee = db.Column(db.Numeric(10,2), default=0.00)
    is_approved      = db.Column(db.Boolean, default=False)
    is_available     = db.Column(db.Boolean, default=True)
    rating           = db.Column(db.Numeric(3,2), default=0.00)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # Appointments where this person is the therapist
    appointments = db.relationship('Appointment',
                                   foreign_keys='Appointment.therapist_id',
                                   backref='therapist', lazy=True)

    def __repr__(self):
        return f'<Therapist {self.user_id}>'


# ======================================================================
# APPOINTMENT MODEL
# ======================================================================
class Appointment(db.Model):
    """Therapy session booking between a user and a therapist."""
    __tablename__ = 'appointments'

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    therapist_id     = db.Column(db.Integer, db.ForeignKey('therapists.id'), nullable=False)
    appointment_date = db.Column(db.Date,    nullable=False)
    appointment_time = db.Column(db.Time,    nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    session_type     = db.Column(db.Enum('online','in-person'), default='online')
    status           = db.Column(
                          db.Enum('pending','confirmed','completed','cancelled'),
                          default='pending')
    notes            = db.Column(db.Text)
    meeting_link     = db.Column(db.String(255))
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.id} — {self.status}>'


# ======================================================================
# MESSAGE MODEL
# ======================================================================
class Message(db.Model):
    """Secure user-to-therapist (and vice-versa) messaging."""
    __tablename__ = 'messages'

    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    sent_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id}>'


# ======================================================================
# MOOD LOG MODEL
# ======================================================================
class MoodLog(db.Model):
    """Daily emoji-based mood tracking entry."""
    __tablename__ = 'mood_logs'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood_score  = db.Column(db.Integer, nullable=False)   # 1–5
    mood_label  = db.Column(db.String(50))                # 'Happy', 'Sad', etc.
    mood_emoji  = db.Column(db.String(10))                # '😊', '😢', etc.
    notes       = db.Column(db.Text)
    logged_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MoodLog {self.mood_label} — {self.logged_date}>'


# ======================================================================
# JOURNAL ENTRY MODEL
# ======================================================================
class JournalEntry(db.Model):
    """Personal mental wellness journal entry."""
    __tablename__ = 'journal_entries'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(200))
    content    = db.Column(db.Text, nullable=False)
    mood_score = db.Column(db.Integer)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<JournalEntry {self.title}>'


# ======================================================================
# RESOURCE MODEL
# ======================================================================
class Resource(db.Model):
    """Mental health article / guide published by admin."""
    __tablename__ = 'resources'

    id           = db.Column(db.Integer, primary_key=True)
    admin_id     = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    content      = db.Column(db.Text, nullable=False)
    category     = db.Column(
                       db.Enum('article','self-help','wellness','motivational','guide'),
                       default='article')
    image_url    = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    views        = db.Column(db.Integer, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Resource {self.title}>'
