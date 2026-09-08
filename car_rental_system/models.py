# ============================================
# models.py - Database Helper Functions
# ============================================

from werkzeug.security import generate_password_hash, check_password_hash


# ============================================
# USER (CUSTOMER) FUNCTIONS
# ============================================

def get_all_users(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cur.fetchall()
    cur.close()
    return users


def get_user_by_id(mysql, user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return user


def get_user_by_email(mysql, email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    return user


def register_user(mysql, full_name, email, phone, password):
    hashed_password = generate_password_hash(password)
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO users (full_name, email, phone, password) VALUES (%s, %s, %s, %s)",
        (full_name, email, phone, hashed_password)
    )
    mysql.connection.commit()
    cur.close()


def verify_user_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)


def delete_user(mysql, user_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cur.close()


# ============================================
# ADMIN FUNCTIONS
# ============================================

def get_admin_by_username(mysql, username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
    admin = cur.fetchone()
    cur.close()
    return admin


def create_default_admin(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as count FROM admins")
    result = cur.fetchone()
    if result['count'] == 0:
        hashed = generate_password_hash('admin123')
        cur.execute(
            "INSERT INTO admins (username, password) VALUES (%s, %s)",
            ('admin', hashed)
        )
        mysql.connection.commit()
    cur.close()


# ============================================
# CAR FUNCTIONS
# ============================================

def get_all_cars(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cars ORDER BY created_at DESC")
    cars = cur.fetchall()
    cur.close()
    return cars


def get_available_cars(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cars WHERE status = 'available' ORDER BY price_per_day ASC")
    cars = cur.fetchall()
    cur.close()
    return cars


def get_car_by_id(mysql, car_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cars WHERE id = %s", (car_id,))
    car = cur.fetchone()
    cur.close()
    return car


def add_car(mysql, name, brand, model, year, color, plate_number, category, tier, seats, price_per_day, description, image_url=None):
    cur = mysql.connection.cursor()
    cur.execute(
        """INSERT INTO cars (name, brand, model, year, color, plate_number, category, tier, seats, price_per_day, description, image_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (name, brand, model, year, color, plate_number, category, tier, seats, price_per_day, description, image_url)
    )
    mysql.connection.commit()
    cur.close()


def update_car(mysql, car_id, name, brand, model, year, color, plate_number, category, tier, seats, price_per_day, description, status, image_url=None):
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE cars SET name=%s, brand=%s, model=%s, year=%s, color=%s,
           plate_number=%s, category=%s, tier=%s, seats=%s, price_per_day=%s,
           description=%s, status=%s, image_url=%s WHERE id=%s""",
        (name, brand, model, year, color, plate_number, category, tier, seats, price_per_day, description, status, image_url, car_id)
    )
    mysql.connection.commit()
    cur.close()


def delete_car(mysql, car_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM cars WHERE id = %s", (car_id,))
    mysql.connection.commit()
    cur.close()


def update_car_status(mysql, car_id, status):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE cars SET status = %s WHERE id = %s", (status, car_id))
    mysql.connection.commit()
    cur.close()


# ============================================
# BOOKING FUNCTIONS
# ============================================

def create_booking(mysql, user_id, car_id, pickup_date, return_date, total_days, total_price, pickup_location):
    cur = mysql.connection.cursor()
    cur.execute(
        """INSERT INTO bookings (user_id, car_id, pickup_date, return_date, total_days, total_price, pickup_location)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (user_id, car_id, pickup_date, return_date, total_days, total_price, pickup_location)
    )
    cur.execute("UPDATE cars SET status = 'rented' WHERE id = %s", (car_id,))
    mysql.connection.commit()
    cur.close()


def get_user_bookings(mysql, user_id):
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT b.*, c.name as car_name, c.brand, c.model, c.plate_number, c.image_url
           FROM bookings b
           JOIN cars c ON b.car_id = c.id
           WHERE b.user_id = %s
           ORDER BY b.created_at DESC""",
        (user_id,)
    )
    bookings = cur.fetchall()
    cur.close()
    return bookings


def get_all_bookings(mysql):
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT b.*, u.full_name, u.email, c.name as car_name, c.plate_number
           FROM bookings b
           JOIN users u ON b.user_id = u.id
           JOIN cars c ON b.car_id = c.id
           ORDER BY b.created_at DESC"""
    )
    bookings = cur.fetchall()
    cur.close()
    return bookings


def update_booking_status(mysql, booking_id, status):
    cur = mysql.connection.cursor()
    cur.execute("SELECT car_id FROM bookings WHERE id = %s", (booking_id,))
    booking = cur.fetchone()
    cur.execute("UPDATE bookings SET status = %s WHERE id = %s", (status, booking_id))
    if status in ('completed', 'cancelled') and booking:
        cur.execute("UPDATE cars SET status = 'available' WHERE id = %s", (booking['car_id'],))
    mysql.connection.commit()
    cur.close()


def cancel_booking(mysql, booking_id, user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
    booking = cur.fetchone()
    if booking:
        cur.execute("UPDATE bookings SET status = 'cancelled' WHERE id = %s", (booking_id,))
        cur.execute("UPDATE cars SET status = 'available' WHERE id = %s", (booking['car_id'],))
        mysql.connection.commit()
    cur.close()
    return booking is not None


# ============================================
# DASHBOARD / STATISTICS FUNCTIONS
# ============================================

def get_dashboard_stats(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as count FROM users")
    total_users = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM cars")
    total_cars = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM cars WHERE status = 'available'")
    available_cars = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM bookings")
    total_bookings = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM bookings WHERE status IN ('pending', 'confirmed')")
    active_bookings = cur.fetchone()['count']
    cur.execute("SELECT COALESCE(SUM(total_price), 0) as revenue FROM bookings WHERE status = 'completed'")
    total_revenue = cur.fetchone()['revenue']
    cur.close()
    return {
        'total_users': total_users,
        'total_cars': total_cars,
        'available_cars': available_cars,
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'total_revenue': total_revenue
    }