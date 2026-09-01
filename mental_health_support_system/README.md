# 🧠 MindSpace — Online Therapy & Mental Health Support System

> **Final Year Project** — Design and Implementation of a Web-Based Online Therapy and Mental Health Support System

A modern, full-stack web application built with **Python Flask**, **MySQL**, **Bootstrap 5**, and a premium **Black & Gold** UI theme.

---

## 📋 Project Overview

MindSpace is a secure, responsive mental health platform that connects users with certified therapists. It provides mood tracking, journaling, resource access, and private messaging — all in one clean, professional interface.

---

## 🗂️ Project Structure

```
mental_health_support_system/
│
├── static/
│   ├── css/style.css          ← Black & Gold theme
│   ├── js/script.js           ← Charts, animations, interactions
│   ├── images/                ← Static images
│   └── uploads/               ← User profile pictures
│
├── templates/
│   ├── base.html              ← Main layout (navbar, sidebar, footer)
│   ├── index.html             ← Homepage
│   ├── login.html             ← User login
│   ├── register.html          ← User / therapist registration
│   ├── dashboard.html         ← User dashboard
│   ├── profile.html           ← Profile & password management
│   ├── appointments.html      ← Appointment list
│   ├── book_appointment.html  ← Booking form
│   ├── resources.html         ← Resources listing
│   ├── resource_detail.html   ← Single resource view
│   ├── therapists.html        ← Therapist directory
│   ├── mood_tracker.html      ← Mood tracker + chart
│   ├── journal.html           ← Journal entries list
│   ├── new_journal.html       ← New journal entry
│   ├── chat.html              ← Messaging system
│   ├── about.html             ← About page
│   └── admin/
│       ├── base_admin.html    ← Admin layout
│       ├── login.html         ← Admin login
│       ├── dashboard.html     ← Admin overview
│       ├── users.html         ← User management
│       ├── therapists.html    ← Therapist approval
│       ├── appointments.html  ← Appointment management
│       ├── resources.html     ← Resource management
│       └── new_resource.html  ← Publish resource
│
├── app.py                     ← Flask app factory & entry point
├── models.py                  ← SQLAlchemy ORM models
├── routes.py                  ← All blueprints & route handlers
├── config.py                  ← App configuration
├── database.sql               ← Raw MySQL schema
├── requirements.txt           ← Python dependencies
└── README.md                  ← This file
```

---

## 🗄️ Database Design

| Table            | Description                                      |
|------------------|--------------------------------------------------|
| `users`          | All registered users (patients + therapists)     |
| `admins`         | Platform administrators                          |
| `therapists`     | Extended therapist profiles linked to users      |
| `appointments`   | Therapy session bookings                         |
| `messages`       | User ↔ therapist secure messages                 |
| `mood_logs`      | Daily emoji-based mood entries                   |
| `journal_entries`| Private personal journal entries                 |
| `resources`      | Mental health articles & guides by admin         |

### Relationships
- `therapists.user_id` → `users.id` (one-to-one)
- `appointments.user_id` → `users.id` (many-to-one)
- `appointments.therapist_id` → `therapists.id` (many-to-one)
- `messages.sender_id` / `receiver_id` → `users.id`
- `mood_logs.user_id` → `users.id`
- `journal_entries.user_id` → `users.id`
- `resources.admin_id` → `admins.id`

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### Step 1 — Clone / Download the project
```bash
cd mental_health_support_system
```

### Step 2 — Create a virtual environment
```bash
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up the MySQL database
```sql
-- In MySQL Workbench or terminal:
CREATE DATABASE mental_health_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 5 — Configure database credentials
Open `config.py` and update:
```python
MYSQL_USER     = 'your_mysql_username'   # e.g. 'root'
MYSQL_PASSWORD = 'your_mysql_password'
MYSQL_DB       = 'mental_health_db'
```

### Step 6 — Run the application
```bash
python app.py
```

Flask will automatically:
- Create all database tables
- Seed a default admin account

### Step 7 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🔐 Default Credentials

### Admin Login
| Field    | Value                     |
|----------|---------------------------|
| URL      | `/auth/admin/login`       |
| Email    | `admin@mentalhealth.com`  |
| Password | `Admin@1234`              |

> ⚠️ Change this password immediately after first login in production.

---

## 🧩 System Modules

### 1. User Module
- Register as patient or therapist
- Secure login with bcrypt password hashing
- Session management with Flask-Login
- Profile editing with photo upload
- Password change

### 2. Therapy Booking Module
- Browse approved therapists
- Book sessions (date, time, online/in-person)
- View appointment history with status tracking
- Cancel pending appointments

### 3. Mental Health Resources
- Articles, self-help guides, wellness tips
- Category-based filtering
- View counter per resource
- Admin publishes / deletes resources

### 4. Mood Tracker
- Emoji-based daily mood logging (1–5 scale)
- One entry per day (updates if re-logged)
- Line chart visualisation with Chart.js
- Full mood history table

### 5. Journal Module
- Private personal journal entries
- Optional mood tag per entry
- Create and delete entries

### 6. Messaging System
- User ↔ therapist secure messaging
- Conversation threads per contact
- Unread message tracking
- Auto-scroll to latest message

### 7. Admin Panel
- Dashboard with platform statistics
- User management (activate/suspend)
- Therapist approval workflow
- Appointment status management + meeting link assignment
- Resource publishing and deletion

---

## 🎨 Design System

| Token          | Value          |
|----------------|----------------|
| Background     | `#0a0a0a`      |
| Card surface   | `#161616`      |
| Gold accent    | `#d4af37`      |
| Gold hover     | `#e8c84a`      |
| Body text      | `#f5f5f5`      |
| Muted text     | `#aaaaaa`      |
| Border         | `rgba(212,175,55,0.2)` |
| Display font   | Cormorant Garamond |
| Body font      | DM Sans        |

---

## 🛡️ Security Features

- **bcrypt** password hashing (no plain-text passwords stored)
- **Flask-Login** session management
- **CSRF-safe** form handling
- File upload validation (extension + size limits)
- Admin-only routes protected by custom decorator
- User account suspension by admin

---

## 📦 Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python 3 / Flask 3      |
| Database   | MySQL 8 + SQLAlchemy    |
| Frontend   | HTML5, CSS3, Bootstrap 5|
| Charts     | Chart.js                |
| Icons      | Bootstrap Icons         |
| Fonts      | Google Fonts            |
| Auth       | Flask-Login + Bcrypt    |

---

## 👨‍🎓 Academic Information

- **Project Title:** Design and Implementation of a Web-Based Online Therapy and Mental Health Support System
- **Technology:** Python Flask, MySQL, Bootstrap 5
- **Purpose:** Final Year Project (Computer Science / Information Technology)

---

*Built with ❤️ for mental wellness awareness.*
