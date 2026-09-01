"""
routes.py — All Flask Blueprints & Route Handlers
===================================================
Organised into blueprints:
  main_bp        → public pages (home, about)
  auth_bp        → register, login, logout
  dashboard_bp   → user dashboard
  appointment_bp → book / manage appointments
  resource_bp    → mental health resources
  mood_bp        → mood tracker
  journal_bp     → journal entries
  message_bp     → messaging system
  admin_bp       → admin panel
"""

import os
from datetime import datetime, date
from functools import wraps

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session, jsonify, current_app)
from flask_login import (login_user, logout_user, login_required,
                          current_user)
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt

from models import db, User, Admin, Therapist, Appointment, Message, MoodLog, JournalEntry, Resource

bcrypt = Bcrypt()

# ── Helper: allowed file extensions ──────────────────────────────────
def allowed_file(filename):
    ext = {'png','jpg','jpeg','gif','webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ext


# ── Helper: admin-only decorator ─────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated


# ======================================================================
# BLUEPRINT: main_bp — Public pages
# ======================================================================
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    resources = Resource.query.filter_by(is_published=True).order_by(Resource.created_at.desc()).limit(3).all()
    therapists = (Therapist.query
                  .filter_by(is_approved=True, is_available=True)
                  .limit(4).all())
    return render_template('index.html', resources=resources, therapists=therapists)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/therapists')
def therapists():
    all_therapists = (Therapist.query
                      .filter_by(is_approved=True, is_available=True)
                      .all())
    return render_template('therapists.html', therapists=all_therapists)


# ======================================================================
# BLUEPRINT: auth_bp — Authentication
# ======================================================================
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        username  = request.form.get('username','').strip()
        email     = request.form.get('email','').strip()
        password  = request.form.get('password','')
        confirm   = request.form.get('confirm_password','')
        full_name = request.form.get('full_name','').strip()
        role      = request.form.get('role','user')   # 'user' or 'therapist'

        # ── Validation ────────────────────────────────────────────────
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email,
                    password=hashed, full_name=full_name, role=role)
        db.session.add(user)
        db.session.flush()   # get user.id before commit

        # If registering as therapist, create therapist profile
        if role == 'therapist':
            specialization   = request.form.get('specialization','')
            license_number   = request.form.get('license_number','')
            years_experience = int(request.form.get('years_experience', 0))
            therapist = Therapist(
                user_id=user.id,
                specialization=specialization,
                license_number=license_number,
                years_experience=years_experience
            )
            db.session.add(therapist)

        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email    = request.form.get('email','').strip()
        password = request.form.get('password','')
        remember = 'remember' in request.form

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if not user.is_active:
                flash('Your account has been suspended.', 'danger')
                return render_template('login.html')
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            return redirect(next_page or url_for('dashboard.home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email    = request.form.get('email','').strip()
        password = request.form.get('password','')
        admin = Admin.query.filter_by(email=email).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin/login.html')


# ======================================================================
# BLUEPRINT: dashboard_bp — User Dashboard
# ======================================================================
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def home():
    # Upcoming appointments
    upcoming = (Appointment.query
                .filter_by(user_id=current_user.id)
                .filter(Appointment.status.in_(['pending','confirmed']))
                .order_by(Appointment.appointment_date)
                .limit(3).all())

    # Recent mood logs
    recent_moods = (MoodLog.query
                    .filter_by(user_id=current_user.id)
                    .order_by(MoodLog.logged_date.desc())
                    .limit(7).all())

    # Unread messages count
    unread_count = (Message.query
                    .filter_by(receiver_id=current_user.id, is_read=False)
                    .count())

    # Latest resources
    resources = (Resource.query
                 .filter_by(is_published=True)
                 .order_by(Resource.created_at.desc())
                 .limit(3).all())

    return render_template('dashboard.html',
                           upcoming=upcoming,
                           recent_moods=recent_moods,
                           unread_count=unread_count,
                           resources=resources)


@dashboard_bp.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name     = request.form.get('full_name','')
        current_user.phone         = request.form.get('phone','')
        current_user.bio           = request.form.get('bio','')
        current_user.gender        = request.form.get('gender','')
        dob_str = request.form.get('date_of_birth','')
        if dob_str:
            try:
                current_user.date_of_birth = datetime.strptime(dob_str,'%Y-%m-%d').date()
            except ValueError:
                pass

        # Profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                current_user.profile_picture = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard.profile'))

    return render_template('profile.html', user=current_user)


@dashboard_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_pw  = request.form.get('old_password','')
    new_pw  = request.form.get('new_password','')
    confirm = request.form.get('confirm_password','')

    if not bcrypt.check_password_hash(current_user.password, old_pw):
        flash('Current password is incorrect.', 'danger')
    elif new_pw != confirm:
        flash('New passwords do not match.', 'danger')
    else:
        current_user.password = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        db.session.commit()
        flash('Password changed successfully!', 'success')

    return redirect(url_for('dashboard.profile'))


# ======================================================================
# BLUEPRINT: appointment_bp — Therapy Booking
# ======================================================================
appointment_bp = Blueprint('appointments', __name__)

@appointment_bp.route('/')
@login_required
def list_appointments():
    appts = (Appointment.query
             .filter_by(user_id=current_user.id)
             .order_by(Appointment.appointment_date.desc())
             .all())
    return render_template('appointments.html', appointments=appts)


@appointment_bp.route('/book', methods=['GET','POST'])
@login_required
def book():
    therapists = Therapist.query.filter_by(is_approved=True, is_available=True).all()

    if request.method == 'POST':
        therapist_id     = request.form.get('therapist_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        session_type     = request.form.get('session_type','online')
        notes            = request.form.get('notes','')

        if not all([therapist_id, appointment_date, appointment_time]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('book_appointment.html', therapists=therapists)

        appt = Appointment(
            user_id          = current_user.id,
            therapist_id     = int(therapist_id),
            appointment_date = datetime.strptime(appointment_date,'%Y-%m-%d').date(),
            appointment_time = datetime.strptime(appointment_time,'%H:%M').time(),
            session_type     = session_type,
            notes            = notes,
            status           = 'pending'
        )
        db.session.add(appt)
        db.session.commit()
        flash('Appointment booked! Awaiting confirmation.', 'success')
        return redirect(url_for('appointments.list_appointments'))

    return render_template('book_appointment.html', therapists=therapists)


@appointment_bp.route('/cancel/<int:appt_id>', methods=['POST'])
@login_required
def cancel(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.user_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('appointments.list_appointments'))
    appt.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('appointments.list_appointments'))


# ======================================================================
# BLUEPRINT: resource_bp — Mental Health Resources
# ======================================================================
resource_bp = Blueprint('resources', __name__)

@resource_bp.route('/')
def list_resources():
    category = request.args.get('category','')
    query    = Resource.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    resources = query.order_by(Resource.created_at.desc()).all()
    return render_template('resources.html', resources=resources, active_cat=category)


@resource_bp.route('/<int:resource_id>')
def view_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    resource.views += 1
    db.session.commit()
    return render_template('resource_detail.html', resource=resource)


# ======================================================================
# BLUEPRINT: mood_bp — Mood Tracker
# ======================================================================
mood_bp = Blueprint('mood', __name__)

MOOD_MAP = {
    1: ('Terrible',  '😞'),
    2: ('Sad',       '😢'),
    3: ('Okay',      '😐'),
    4: ('Good',      '😊'),
    5: ('Excellent', '😄'),
}

@mood_bp.route('/')
@login_required
def tracker():
    logs = (MoodLog.query
            .filter_by(user_id=current_user.id)
            .order_by(MoodLog.logged_date.desc())
            .limit(30).all())

    # Build chart data (last 7 entries)
    chart_labels  = [str(m.logged_date) for m in reversed(logs[:7])]
    chart_scores  = [m.mood_score       for m in reversed(logs[:7])]

    today_log = MoodLog.query.filter_by(
        user_id=current_user.id,
        logged_date=date.today()
    ).first()

    return render_template('mood_tracker.html',
                           logs=logs,
                           chart_labels=chart_labels,
                           chart_scores=chart_scores,
                           today_log=today_log,
                           mood_map=MOOD_MAP)


@mood_bp.route('/log', methods=['POST'])
@login_required
def log_mood():
    score = int(request.form.get('mood_score', 3))
    notes = request.form.get('notes','')
    label, emoji = MOOD_MAP.get(score, ('Okay','😐'))

    # Only one entry per day
    existing = MoodLog.query.filter_by(
        user_id=current_user.id,
        logged_date=date.today()
    ).first()

    if existing:
        existing.mood_score = score
        existing.mood_label = label
        existing.mood_emoji = emoji
        existing.notes      = notes
    else:
        log = MoodLog(user_id=current_user.id, mood_score=score,
                      mood_label=label, mood_emoji=emoji,
                      notes=notes, logged_date=date.today())
        db.session.add(log)

    db.session.commit()
    flash(f'Mood logged: {emoji} {label}', 'success')
    return redirect(url_for('mood.tracker'))


# ======================================================================
# BLUEPRINT: journal_bp — Journal Entries
# ======================================================================
journal_bp = Blueprint('journal', __name__)

@journal_bp.route('/')
@login_required
def list_entries():
    entries = (JournalEntry.query
               .filter_by(user_id=current_user.id)
               .order_by(JournalEntry.created_at.desc())
               .all())
    return render_template('journal.html', entries=entries)


@journal_bp.route('/new', methods=['GET','POST'])
@login_required
def new_entry():
    if request.method == 'POST':
        title   = request.form.get('title','Untitled')
        content = request.form.get('content','')
        mood    = request.form.get('mood_score')

        entry = JournalEntry(
            user_id    = current_user.id,
            title      = title,
            content    = content,
            mood_score = int(mood) if mood else None
        )
        db.session.add(entry)
        db.session.commit()
        flash('Journal entry saved.', 'success')
        return redirect(url_for('journal.list_entries'))

    return render_template('new_journal.html')


@journal_bp.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('journal.list_entries'))
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted.', 'info')
    return redirect(url_for('journal.list_entries'))


# ======================================================================
# BLUEPRINT: message_bp — Messaging System
# ======================================================================
message_bp = Blueprint('messages', __name__)

@message_bp.route('/')
@login_required
def inbox():
    # Get unique conversations
    sent_to     = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id).distinct()
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id).distinct()
    contact_ids = set([r[0] for r in sent_to] + [r[0] for r in received_from])
    contacts    = User.query.filter(User.id.in_(contact_ids)).all()
    return render_template('chat.html', contacts=contacts, messages=[], active_contact=None)


@message_bp.route('/conversation/<int:contact_id>')
@login_required
def conversation(contact_id):
    contact  = User.query.get_or_404(contact_id)
    messages = (Message.query
                .filter(
                    db.or_(
                        db.and_(Message.sender_id==current_user.id,   Message.receiver_id==contact_id),
                        db.and_(Message.sender_id==contact_id,        Message.receiver_id==current_user.id)
                    ))
                .order_by(Message.sent_at.asc())
                .all())

    # Mark received messages as read
    Message.query.filter_by(sender_id=contact_id,
                             receiver_id=current_user.id,
                             is_read=False).update({'is_read': True})
    db.session.commit()

    # Build contacts list for sidebar
    sent_to      = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id).distinct()
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id).distinct()
    contact_ids  = set([r[0] for r in sent_to] + [r[0] for r in received_from])
    contact_ids.add(contact_id)
    contacts = User.query.filter(User.id.in_(contact_ids)).all()

    return render_template('chat.html', contacts=contacts,
                           messages=messages, active_contact=contact)


@message_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id')
    content     = request.form.get('content','').strip()

    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('messages.conversation', contact_id=receiver_id))

    msg = Message(sender_id=current_user.id,
                  receiver_id=int(receiver_id),
                  content=content)
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for('messages.conversation', contact_id=receiver_id))


# ======================================================================
# BLUEPRINT: admin_bp — Admin Panel
# ======================================================================
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'users'        : User.query.count(),
        'therapists'   : Therapist.query.count(),
        'appointments' : Appointment.query.count(),
        'resources'    : Resource.query.count(),
        'pending_appts': Appointment.query.filter_by(status='pending').count(),
        'pending_therapists': Therapist.query.filter_by(is_approved=False).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_appts = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_users=recent_users, recent_appts=recent_appts)


@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'suspended'
    flash(f'User {user.username} has been {status}.', 'info')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/therapists')
@admin_required
def manage_therapists():
    therapists = Therapist.query.all()
    return render_template('admin/therapists.html', therapists=therapists)


@admin_bp.route('/therapists/approve/<int:t_id>', methods=['POST'])
@admin_required
def approve_therapist(t_id):
    t = Therapist.query.get_or_404(t_id)
    t.is_approved = True
    db.session.commit()
    flash('Therapist approved!', 'success')
    return redirect(url_for('admin.manage_therapists'))


@admin_bp.route('/therapists/reject/<int:t_id>', methods=['POST'])
@admin_required
def reject_therapist(t_id):
    t = Therapist.query.get_or_404(t_id)
    t.is_approved = False
    db.session.commit()
    flash('Therapist rejected.', 'warning')
    return redirect(url_for('admin.manage_therapists'))


@admin_bp.route('/appointments')
@admin_required
def manage_appointments():
    appts = Appointment.query.order_by(Appointment.appointment_date.desc()).all()
    return render_template('admin/appointments.html', appointments=appts)


@admin_bp.route('/appointments/update/<int:appt_id>', methods=['POST'])
@admin_required
def update_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = request.form.get('status', appt.status)
    appt.meeting_link = request.form.get('meeting_link', appt.meeting_link)
    db.session.commit()
    flash('Appointment updated.', 'success')
    return redirect(url_for('admin.manage_appointments'))


@admin_bp.route('/resources')
@admin_required
def manage_resources():
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return render_template('admin/resources.html', resources=resources)


@admin_bp.route('/resources/new', methods=['GET','POST'])
@admin_required
def new_resource():
    if request.method == 'POST':
        title    = request.form.get('title','')
        content  = request.form.get('content','')
        category = request.form.get('category','article')

        resource = Resource(admin_id=current_user.id,
                            title=title, content=content, category=category)
        db.session.add(resource)
        db.session.commit()
        flash('Resource published!', 'success')
        return redirect(url_for('admin.manage_resources'))
    return render_template('admin/new_resource.html')


@admin_bp.route('/resources/delete/<int:r_id>', methods=['POST'])
@admin_required
def delete_resource(r_id):
    resource = Resource.query.get_or_404(r_id)
    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted.', 'info')
    return redirect(url_for('admin.manage_resources'))


@admin_bp.route('/logout')
def admin_logout():
    logout_user()
    return redirect(url_for('auth.admin_login'))
