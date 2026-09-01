"""
app.py — Flask Application Entry Point
========================================
Initialises the Flask app, registers extensions,
creates database tables, and wires up all blueprints.
"""

from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import active_config
from models import db, User, Admin

# ── Extensions (initialised without app for factory pattern) ──────────
bcrypt       = Bcrypt()
login_manager = LoginManager()


def create_app(config_object=None):
    """Application factory — builds and returns the configured Flask app."""
    app = Flask(__name__)
    app.config.from_object(active_config)

    # ── Bind extensions to app ────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Where to redirect unauthenticated users
    login_manager.login_view        = 'auth.login'
    login_manager.login_message     = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # ── User loader for Flask-Login ───────────────────────────────────
    @login_manager.user_loader
    def load_user(user_id):
        """
        Called on every request to reload the user from the session.
        Handles both regular users and admins using a prefixed ID trick.
        """
        if str(user_id).startswith('admin-'):
            admin_id = int(user_id.split('-')[1])
            return Admin.query.get(admin_id)
        return User.query.get(int(user_id))

    # ── Register blueprints ───────────────────────────────────────────
    from routes import (
        main_bp, auth_bp, dashboard_bp,
        appointment_bp, resource_bp,
        mood_bp, journal_bp, message_bp, admin_bp
    )
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,        url_prefix='/auth')
    app.register_blueprint(dashboard_bp,   url_prefix='/dashboard')
    app.register_blueprint(appointment_bp, url_prefix='/appointments')
    app.register_blueprint(resource_bp,    url_prefix='/resources')
    app.register_blueprint(mood_bp,        url_prefix='/mood')
    app.register_blueprint(journal_bp,     url_prefix='/journal')
    app.register_blueprint(message_bp,     url_prefix='/messages')
    app.register_blueprint(admin_bp,       url_prefix='/admin')

    # ── Custom Jinja2 filters ─────────────────────────────────────────
    from markupsafe import Markup, escape

    @app.template_filter('nl2br')
    def nl2br_filter(value):
        """Convert newlines to <br> tags for safe HTML display."""
        return Markup(escape(value).replace('\n', '<br>\n'))

    # ── Create tables on first run ────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app


def _seed_admin(app):
    """Create a default admin account if none exists."""
    from flask_bcrypt import Bcrypt as _Bcrypt
    _bcrypt = _Bcrypt(app)
    if not Admin.query.first():
        hashed = _bcrypt.generate_password_hash('Admin@1234').decode('utf-8')
        admin  = Admin(username='admin',
                       email='admin@mentalhealth.com',
                       password=hashed)
        db.session.add(admin)
        db.session.commit()
        print("✅  Default admin created  →  admin / Admin@1234")


# ── Run directly ──────────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
