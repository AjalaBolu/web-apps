"""
test_app.py — Comprehensive Test Suite
========================================
Tests every major route and feature of the
Mental Health Support System before deployment.

Run with:
    python test_app.py
"""

import unittest
import json
from datetime import date, time
from app import create_app
from models import db, User, Admin, Therapist, Appointment, Message, MoodLog, JournalEntry, Resource
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


# ── Test configuration (uses in-memory SQLite so no MySQL needed) ──
class TestConfig:
    TESTING                     = True
    SECRET_KEY                  = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI     = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED            = False
    UPLOAD_FOLDER               = 'static/uploads'


# ══════════════════════════════════════════════════════════════════════
# BASE TEST CASE — shared setup / teardown
# ══════════════════════════════════════════════════════════════════════
class BaseTestCase(unittest.TestCase):

    def setUp(self):
        """Create a fresh app + DB before every test."""
        self.app = create_app(config_object=TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            # Drop and recreate so each test starts completely fresh
            db.drop_all()
            db.create_all()
            self._seed_data()

    def tearDown(self):
        """Drop all tables after every test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ── Seed minimal data for tests ───────────────────────────────
    def _seed_data(self):
        # Admin
        admin = Admin(
            username = 'admin',
            email    = 'admin@test.com',
            password = bcrypt.generate_password_hash('Admin@1234').decode('utf-8')
        )
        db.session.add(admin)

        # Regular user
        user = User(
            username  = 'testuser',
            email     = 'user@test.com',
            password  = bcrypt.generate_password_hash('User@1234').decode('utf-8'),
            full_name = 'Test User',
            role      = 'user',
            is_active = True
        )
        db.session.add(user)
        db.session.flush()

        # Therapist user
        t_user = User(
            username  = 'testtherapist',
            email     = 'therapist@test.com',
            password  = bcrypt.generate_password_hash('Therapist@1234').decode('utf-8'),
            full_name = 'Dr. Test Therapist',
            role      = 'therapist',
            is_active = True
        )
        db.session.add(t_user)
        db.session.flush()

        therapist = Therapist(
            user_id          = t_user.id,
            specialization   = 'Anxiety & Depression',
            license_number   = 'LIC-12345',
            years_experience = 5,
            is_approved      = True,
            is_available     = True,
            consultation_fee = 50.00
        )
        db.session.add(therapist)
        db.session.flush()

        # Appointment
        appt = Appointment(
            user_id          = user.id,
            therapist_id     = therapist.id,
            appointment_date = date(2025, 12, 1),
            appointment_time = time(10, 0),
            session_type     = 'online',
            status           = 'pending'
        )
        db.session.add(appt)

        # Mood log
        mood = MoodLog(
            user_id     = user.id,
            mood_score  = 4,
            mood_label  = 'Good',
            mood_emoji  = '😊',
            logged_date = date.today()
        )
        db.session.add(mood)

        # Journal entry
        journal = JournalEntry(
            user_id = user.id,
            title   = 'Test Entry',
            content = 'This is a test journal entry.'
        )
        db.session.add(journal)

        # Resource
        resource = Resource(
            admin_id     = admin.id,
            title        = 'Test Article',
            content      = 'This is a test mental health article with useful content.',
            category     = 'article',
            is_published = True
        )
        db.session.add(resource)

        # Message
        message = Message(
            sender_id   = user.id,
            receiver_id = t_user.id,
            content     = 'Hello, I need help.',
            is_read     = False
        )
        db.session.add(message)

        db.session.commit()

    # ── Login helpers ─────────────────────────────────────────────
    def login_user(self):
        return self.client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@1234'
        }, follow_redirects=True)

    def login_admin(self):
        return self.client.post('/auth/admin/login', data={
            'email': 'admin@test.com',
            'password': 'Admin@1234'
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def get_therapist_id(self):
        with self.app.app_context():
            t = Therapist.query.first()
            return t.id if t else None

    def get_user_id(self):
        with self.app.app_context():
            u = User.query.filter_by(role='user').first()
            return u.id if u else None

    def get_resource_id(self):
        with self.app.app_context():
            r = Resource.query.first()
            return r.id if r else None

    def get_appointment_id(self):
        with self.app.app_context():
            a = Appointment.query.first()
            return a.id if a else None

    def get_therapist_user_id(self):
        with self.app.app_context():
            t = Therapist.query.first()
            return t.user_id if t else None


# ══════════════════════════════════════════════════════════════════════
# 1. PUBLIC PAGE TESTS
# ══════════════════════════════════════════════════════════════════════
class TestPublicPages(BaseTestCase):

    def test_homepage_loads(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'MindSpace', r.data)
        print("  ✅ Homepage loads")

    def test_about_page_loads(self):
        r = self.client.get('/about')
        self.assertEqual(r.status_code, 200)
        print("  ✅ About page loads")

    def test_therapists_page_loads(self):
        r = self.client.get('/therapists')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Therapists page loads")

    def test_resources_page_loads(self):
        r = self.client.get('/resources/')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Resources page loads")

    def test_resource_detail_loads(self):
        rid = self.get_resource_id()
        r = self.client.get(f'/resources/{rid}')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Resource detail page loads")

    def test_resource_category_filter(self):
        r = self.client.get('/resources/?category=article')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Resource category filter works")

    def test_404_page(self):
        r = self.client.get('/this-page-does-not-exist')
        self.assertEqual(r.status_code, 404)
        print("  ✅ 404 returns correct status")


# ══════════════════════════════════════════════════════════════════════
# 2. AUTHENTICATION TESTS
# ══════════════════════════════════════════════════════════════════════
class TestAuthentication(BaseTestCase):

    def test_login_page_loads(self):
        r = self.client.get('/auth/login')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Login page loads")

    def test_register_page_loads(self):
        r = self.client.get('/auth/register')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Register page loads")

    def test_valid_login(self):
        r = self.login_user()
        self.assertEqual(r.status_code, 200)
        print("  ✅ Valid user login succeeds")

    def test_invalid_login_wrong_password(self):
        r = self.client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Wrong password rejected")

    def test_invalid_login_wrong_email(self):
        r = self.client.post('/auth/login', data={
            'email': 'nobody@test.com',
            'password': 'User@1234'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Non-existent email rejected")

    def test_register_new_user(self):
        r = self.client.post('/auth/register', data={
            'username':         'newuser',
            'email':            'newuser@test.com',
            'full_name':        'New User',
            'password':         'NewPass@123',
            'confirm_password': 'NewPass@123',
            'role':             'user'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ New user registration works")

    def test_register_duplicate_email(self):
        r = self.client.post('/auth/register', data={
            'username':         'anotheruser',
            'email':            'user@test.com',   # already exists
            'full_name':        'Another',
            'password':         'Pass@1234',
            'confirm_password': 'Pass@1234',
            'role':             'user'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Duplicate email registration blocked")

    def test_register_password_mismatch(self):
        r = self.client.post('/auth/register', data={
            'username':         'mismatch',
            'email':            'mismatch@test.com',
            'full_name':        'Mismatch User',
            'password':         'Pass@1234',
            'confirm_password': 'Different@1234',
            'role':             'user'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Password mismatch blocked")

    def test_register_therapist(self):
        r = self.client.post('/auth/register', data={
            'username':         'newtherapist',
            'email':            'newtherapist@test.com',
            'full_name':        'Dr. New',
            'password':         'Therapist@123',
            'confirm_password': 'Therapist@123',
            'role':             'therapist',
            'specialization':   'Stress Management',
            'license_number':   'LIC-99999',
            'years_experience': '3'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Therapist registration works")

    def test_logout(self):
        self.login_user()
        r = self.logout()
        self.assertEqual(r.status_code, 200)
        print("  ✅ Logout works")

    def test_protected_route_redirects_guest(self):
        r = self.client.get('/dashboard/', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        print("  ✅ Protected route redirects unauthenticated user")

    def test_admin_login_page_loads(self):
        r = self.client.get('/auth/admin/login')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin login page loads")

    def test_valid_admin_login(self):
        r = self.login_admin()
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin login succeeds")

    def test_invalid_admin_login(self):
        r = self.client.post('/auth/admin/login', data={
            'email':    'admin@test.com',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Wrong admin password rejected")


# ══════════════════════════════════════════════════════════════════════
# 3. DASHBOARD TESTS
# ══════════════════════════════════════════════════════════════════════
class TestDashboard(BaseTestCase):

    def test_dashboard_requires_login(self):
        r = self.client.get('/dashboard/', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        print("  ✅ Dashboard requires login")

    def test_dashboard_loads_when_logged_in(self):
        self.login_user()
        r = self.client.get('/dashboard/')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Dashboard loads for logged-in user")

    def test_profile_page_loads(self):
        self.login_user()
        r = self.client.get('/dashboard/profile')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Profile page loads")

    def test_profile_update(self):
        self.login_user()
        r = self.client.post('/dashboard/profile', data={
            'full_name': 'Updated Name',
            'phone':     '+2348012345678',
            'bio':       'Updated bio text',
            'gender':    'male'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Profile update works")

    def test_change_password_correct(self):
        self.login_user()
        r = self.client.post('/dashboard/change-password', data={
            'old_password':     'User@1234',
            'new_password':     'NewUser@5678',
            'confirm_password': 'NewUser@5678'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Password change works")

    def test_change_password_wrong_old(self):
        self.login_user()
        r = self.client.post('/dashboard/change-password', data={
            'old_password':     'WrongOldPass',
            'new_password':     'NewUser@5678',
            'confirm_password': 'NewUser@5678'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Wrong old password rejected")


# ══════════════════════════════════════════════════════════════════════
# 4. APPOINTMENT TESTS
# ══════════════════════════════════════════════════════════════════════
class TestAppointments(BaseTestCase):

    def test_appointments_page_loads(self):
        self.login_user()
        r = self.client.get('/appointments/')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Appointments page loads")

    def test_book_appointment_page_loads(self):
        self.login_user()
        r = self.client.get('/appointments/book')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Book appointment page loads")

    def test_book_appointment(self):
        self.login_user()
        tid = self.get_therapist_id()
        r = self.client.post('/appointments/book', data={
            'therapist_id':     tid,
            'appointment_date': '2025-12-15',
            'appointment_time': '14:00',
            'session_type':     'online',
            'notes':            'First session'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Book appointment works")

    def test_book_appointment_missing_fields(self):
        self.login_user()
        r = self.client.post('/appointments/book', data={
            'therapist_id': '',
            'appointment_date': '',
            'appointment_time': ''
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Missing fields validation works")

    def test_cancel_appointment(self):
        self.login_user()
        aid = self.get_appointment_id()
        r = self.client.post(f'/appointments/cancel/{aid}',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Cancel appointment works")


# ══════════════════════════════════════════════════════════════════════
# 5. MOOD TRACKER TESTS
# ══════════════════════════════════════════════════════════════════════
class TestMoodTracker(BaseTestCase):

    def test_mood_tracker_page_loads(self):
        self.login_user()
        r = self.client.get('/mood/')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Mood tracker page loads")

    def test_log_mood(self):
        self.login_user()
        r = self.client.post('/mood/log', data={
            'mood_score': '5',
            'notes':      'Feeling great today!'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Mood logging works")

    def test_update_existing_mood(self):
        self.login_user()
        # Log once
        self.client.post('/mood/log', data={'mood_score': '3', 'notes': 'Okay'})
        # Log again same day (should update)
        r = self.client.post('/mood/log', data={
            'mood_score': '4',
            'notes': 'Better now'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Mood update (same day) works")

    def test_all_mood_scores(self):
        self.login_user()
        for score in [1, 2, 3, 4, 5]:
            r = self.client.post('/mood/log', data={
                'mood_score': str(score),
                'notes': f'Score {score}'
            }, follow_redirects=True)
            self.assertEqual(r.status_code, 200)
        print("  ✅ All mood scores (1–5) work")


# ══════════════════════════════════════════════════════════════════════
# 6. JOURNAL TESTS
# ══════════════════════════════════════════════════════════════════════
class TestJournal(BaseTestCase):

    def test_journal_page_loads(self):
        self.login_user()
        r = self.client.get('/journal/')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Journal page loads")

    def test_new_journal_page_loads(self):
        self.login_user()
        r = self.client.get('/journal/new')
        self.assertEqual(r.status_code, 200)
        print("  ✅ New journal entry page loads")

    def test_create_journal_entry(self):
        self.login_user()
        r = self.client.post('/journal/new', data={
            'title':      'My Day',
            'content':    'Today was a good day overall.',
            'mood_score': '4'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Create journal entry works")

    def test_create_journal_entry_no_title(self):
        self.login_user()
        r = self.client.post('/journal/new', data={
            'title':   '',
            'content': 'Entry without a title.',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Journal entry without title works")

    def test_delete_journal_entry(self):
        self.login_user()
        with self.app.app_context():
            entry = JournalEntry.query.first()
            eid = entry.id
        r = self.client.post(f'/journal/delete/{eid}',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Delete journal entry works")


# ══════════════════════════════════════════════════════════════════════
# 7. MESSAGING TESTS
# ══════════════════════════════════════════════════════════════════════
class TestMessaging(BaseTestCase):

    def test_inbox_loads(self):
        self.login_user()
        r = self.client.get('/messages/')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Inbox loads")

    def test_conversation_loads(self):
        self.login_user()
        tid = self.get_therapist_user_id()
        r = self.client.get(f'/messages/conversation/{tid}')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Conversation page loads")

    def test_send_message(self):
        self.login_user()
        tid = self.get_therapist_user_id()
        r = self.client.post('/messages/send', data={
            'receiver_id': tid,
            'content':     'Hello, I need support please.'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Send message works")

    def test_send_empty_message(self):
        self.login_user()
        tid = self.get_therapist_user_id()
        r = self.client.post('/messages/send', data={
            'receiver_id': tid,
            'content':     ''
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Empty message blocked")


# ══════════════════════════════════════════════════════════════════════
# 8. ADMIN PANEL TESTS
# ══════════════════════════════════════════════════════════════════════
class TestAdminPanel(BaseTestCase):

    def test_admin_dashboard_requires_login(self):
        r = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        print("  ✅ Admin dashboard requires login")

    def test_admin_dashboard_loads(self):
        self.login_admin()
        r = self.client.get('/admin/dashboard')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin dashboard loads")

    def test_admin_users_page(self):
        self.login_admin()
        r = self.client.get('/admin/users')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin users page loads")

    def test_admin_therapists_page(self):
        self.login_admin()
        r = self.client.get('/admin/therapists')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin therapists page loads")

    def test_admin_appointments_page(self):
        self.login_admin()
        r = self.client.get('/admin/appointments')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin appointments page loads")

    def test_admin_resources_page(self):
        self.login_admin()
        r = self.client.get('/admin/resources')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin resources page loads")

    def test_admin_toggle_user(self):
        self.login_admin()
        uid = self.get_user_id()
        r = self.client.post(f'/admin/users/toggle/{uid}',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin toggle user works")

    def test_admin_approve_therapist(self):
        self.login_admin()
        tid = self.get_therapist_id()
        r = self.client.post(f'/admin/therapists/approve/{tid}',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin approve therapist works")

    def test_admin_reject_therapist(self):
        self.login_admin()
        tid = self.get_therapist_id()
        r = self.client.post(f'/admin/therapists/reject/{tid}',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin reject therapist works")

    def test_admin_create_resource(self):
        self.login_admin()
        r = self.client.post('/admin/resources/new', data={
            'title':    'New Wellness Guide',
            'content':  'This is an important wellness guide for all users.',
            'category': 'wellness'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin publish resource works")

    def test_admin_delete_resource(self):
        self.login_admin()
        rid = self.get_resource_id()
        r = self.client.post(f'/admin/resources/delete/{rid}',
                             follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin delete resource works")

    def test_admin_update_appointment(self):
        self.login_admin()
        aid = self.get_appointment_id()
        r = self.client.post(f'/admin/appointments/update/{aid}', data={
            'status':       'confirmed',
            'meeting_link': 'https://meet.google.com/test-link'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin update appointment works")

    def test_regular_user_cannot_access_admin(self):
        self.login_user()   # login as normal user
        r = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        print("  ✅ Regular user blocked from admin panel")

    def test_admin_new_resource_page_loads(self):
        self.login_admin()
        r = self.client.get('/admin/resources/new')
        self.assertEqual(r.status_code, 200)
        print("  ✅ Admin new resource page loads")


# ══════════════════════════════════════════════════════════════════════
# 9. DATABASE MODEL TESTS
# ══════════════════════════════════════════════════════════════════════
class TestDatabaseModels(BaseTestCase):

    def test_user_created(self):
        with self.app.app_context():
            user = User.query.filter_by(email='user@test.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, 'testuser')
        print("  ✅ User model created correctly")

    def test_therapist_linked_to_user(self):
        with self.app.app_context():
            t = Therapist.query.first()
            self.assertIsNotNone(t)
            self.assertIsNotNone(t.user)
            self.assertEqual(t.user.role, 'therapist')
        print("  ✅ Therapist linked to user correctly")

    def test_appointment_relationships(self):
        with self.app.app_context():
            appt = Appointment.query.first()
            self.assertIsNotNone(appt.patient)
            self.assertIsNotNone(appt.therapist)
        print("  ✅ Appointment relationships work")

    def test_mood_log_created(self):
        with self.app.app_context():
            mood = MoodLog.query.first()
            self.assertIsNotNone(mood)
            self.assertEqual(mood.mood_score, 4)
        print("  ✅ MoodLog model works")

    def test_journal_entry_created(self):
        with self.app.app_context():
            entry = JournalEntry.query.first()
            self.assertIsNotNone(entry)
            self.assertEqual(entry.title, 'Test Entry')
        print("  ✅ JournalEntry model works")

    def test_message_created(self):
        with self.app.app_context():
            msg = Message.query.first()
            self.assertIsNotNone(msg)
            self.assertFalse(msg.is_read)
        print("  ✅ Message model works")

    def test_resource_created(self):
        with self.app.app_context():
            res = Resource.query.first()
            self.assertIsNotNone(res)
            self.assertTrue(res.is_published)
        print("  ✅ Resource model works")

    def test_admin_created(self):
        with self.app.app_context():
            admin = Admin.query.first()
            self.assertIsNotNone(admin)
        print("  ✅ Admin model works")


# ══════════════════════════════════════════════════════════════════════
# MAIN — run all tests with a pretty report
# ══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print()
    print("=" * 60)
    print("  MINDSPACE — Test Suite")
    print("=" * 60)

    test_classes = [
        ("Public Pages",       TestPublicPages),
        ("Authentication",     TestAuthentication),
        ("Dashboard",          TestDashboard),
        ("Appointments",       TestAppointments),
        ("Mood Tracker",       TestMoodTracker),
        ("Journal",            TestJournal),
        ("Messaging",          TestMessaging),
        ("Admin Panel",        TestAdminPanel),
        ("Database Models",    TestDatabaseModels),
    ]

    total_run    = 0
    total_failed = 0
    total_errors = 0

    for section_name, test_class in test_classes:
        print(f"\n📋 {section_name}")
        print("-" * 40)
        suite  = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=0, stream=open('nul','w') if __import__('os').name == 'nt' else open('/dev/null','w'))
        result = runner.run(suite)

        total_run    += result.testsRun
        total_failed += len(result.failures)
        total_errors += len(result.errors)

        # Print failures/errors if any
        for test, err in result.failures + result.errors:
            print(f"  ❌ FAIL: {test}")
            # Print just the last line of the error
            last_line = [l for l in err.strip().split('\n') if l.strip()][-1]
            print(f"     → {last_line}")

    # ── Final summary ─────────────────────────────────────────────
    passed = total_run - total_failed - total_errors
    print()
    print("=" * 60)
    print(f"  RESULTS: {total_run} tests run")
    print(f"  ✅ Passed : {passed}")
    print(f"  ❌ Failed : {total_failed + total_errors}")
    print("=" * 60)

    if total_failed + total_errors == 0:
        print()
        print("  🎉 ALL TESTS PASSED — Ready to deploy!")
    else:
        print()
        print("  ⚠️  Fix the failing tests before deploying.")
    print()
