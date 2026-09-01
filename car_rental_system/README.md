# 🚗 DriveEase — Online Car Rental System
**Final Year Project | Python Flask + MySQL**

---

## 📋 Project Overview

DriveEase is a full-stack web application for managing car rentals online. It allows customers to browse, book, and manage vehicle rentals, while administrators can manage the full fleet and booking lifecycle through a dedicated admin panel.

---

## 🏗️ Project Structure

```
car_rental_system/
│
├── static/
│   ├── css/
│   │   ├── style.css        ← Main styles (customer-facing)
│   │   └── admin.css        ← Admin panel styles
│   ├── js/
│   │   └── main.js          ← Frontend JavaScript
│   └── images/              ← Car images (place here)
│
├── templates/
│   ├── layout.html          ← Base layout (navbar, footer)
│   ├── admin_layout.html    ← Admin base (sidebar layout)
│   ├── index.html           ← Homepage
│   ├── cars.html            ← Browse cars page
│   ├── login.html           ← Customer login
│   ├── register.html        ← Customer registration
│   ├── dashboard.html       ← Customer dashboard
│   ├── booking.html         ← Car booking form
│   ├── admin_login.html     ← Admin login
│   ├── admin_dashboard.html ← Admin overview
│   ├── admin_cars.html      ← Manage cars
│   ├── admin_edit_car.html  ← Edit a car
│   ├── admin_bookings.html  ← Manage bookings
│   └── admin_users.html     ← Manage users
│
├── app.py          ← Flask app + DB config
├── models.py       ← Database functions (CRUD)
├── routes.py       ← All URL routes and logic
├── database.sql    ← MySQL schema + seed data
├── requirements.txt
└── README.md
```

---

## 🗃️ Database Design

### Tables & Relationships

```
users          ←────────────── bookings ──────────────→  cars
(id, name,                  (id, user_id, car_id,         (id, name,
 email,                      pickup_date, return_date,      brand, model,
 phone,                      total_days, total_price,       price_per_day,
 password)                   status)                        status)

admins
(id, username, password)
```

**Relationships:**
- One `user` can have many `bookings`
- One `car` can have many `bookings`
- `bookings.user_id` → Foreign Key → `users.id`
- `bookings.car_id`  → Foreign Key → `cars.id`

---

## ⚙️ Installation Guide

### Step 1 — Prerequisites
- Python 3.8+
- MySQL Server
- pip (Python package manager)

### Step 2 — Clone or Download Project
```bash
cd Desktop
# If using git:
git clone <your-repo-url>
cd car_rental_system
```

### Step 3 — Install Python Packages
```bash
pip install -r requirements.txt
```

### Step 4 — Set Up the Database
1. Open MySQL Workbench or run MySQL in terminal:
```bash
mysql -u root -p
```
2. Run the SQL schema:
```sql
source database.sql;
```
Or paste the contents of `database.sql` into your MySQL client.

### Step 5 — Configure Database Credentials
Open `app.py` and update these lines:
```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'       # Your MySQL username
app.config['MYSQL_PASSWORD'] = ''       # Your MySQL password
app.config['MYSQL_DB'] = 'car_rental_db'
```

### Step 6 — Run the Application
```bash
python app.py
```

### Step 7 — Open in Browser
```
http://localhost:5000
```

---

## 🔐 Default Login Credentials

| Role     | Username / Email   | Password   |
|----------|--------------------|------------|
| Customer | Register yourself  | —          |
| Admin    | `admin`            | `admin123` |

> ⚠️ Change the admin password after first login in production!

---

## 🌐 Application Routes

### Customer Routes
| URL                    | Description           |
|------------------------|-----------------------|
| `/`                    | Homepage              |
| `/cars`                | Browse available cars |
| `/register`            | Register new account  |
| `/login`               | Customer login        |
| `/logout`              | Logout                |
| `/dashboard`           | My bookings           |
| `/book/<car_id>`       | Book a specific car   |
| `/cancel_booking/<id>` | Cancel a booking      |

### Admin Routes
| URL                        | Description         |
|----------------------------|---------------------|
| `/admin/login`             | Admin login         |
| `/admin/dashboard`         | Stats overview      |
| `/admin/cars`              | Manage fleet        |
| `/admin/add_car`           | Add new car         |
| `/admin/edit_car/<id>`     | Edit car details    |
| `/admin/delete_car/<id>`   | Delete car          |
| `/admin/bookings`          | All bookings        |
| `/admin/update_booking/<id>` | Change booking status |
| `/admin/users`             | All customers       |
| `/admin/delete_user/<id>`  | Delete customer     |

---

## 🔑 Authentication Flow

1. Customer submits login form (email + password)
2. `routes.py` calls `get_user_by_email()` from `models.py`
3. `verify_user_password()` uses Werkzeug's `check_password_hash()` to compare
4. If correct → user info stored in `session` (secure browser cookie)
5. Protected routes check `if 'user_id' not in session` → redirect to login
6. Logout clears the session with `session.pop()`

**Passwords are NEVER stored in plain text** — Werkzeug's PBKDF2 hash is used.

---

## 💡 Key Features

- ✅ Customer registration & secure login
- ✅ Browse & filter cars by category
- ✅ Live price calculator on booking page
- ✅ Booking history with status tracking
- ✅ Admin sidebar dashboard
- ✅ Add/edit/delete cars via modal
- ✅ Manage and update booking statuses
- ✅ Dashboard statistics (users, revenue, cars)
- ✅ Responsive Bootstrap 5 UI
- ✅ Password hashing for security

---

## 🛠️ Tech Stack

| Layer     | Technology         |
|-----------|--------------------|
| Backend   | Python Flask       |
| Database  | MySQL              |
| ORM       | Flask-MySQLdb      |
| Frontend  | HTML, CSS, Bootstrap 5 |
| JS        | Vanilla JavaScript |
| Auth      | Flask Sessions + Werkzeug |

---

## 👨‍🎓 Final Year Project Notes

This project demonstrates:
- MVC-style architecture (Models, Views, Routes)
- Relational database design with foreign keys
- Secure authentication with password hashing
- CRUD operations (Create, Read, Update, Delete)
- Session-based user authentication
- Responsive UI design with Bootstrap 5

---

*Developed as a Final Year Project — Computer Science / Information Technology*
