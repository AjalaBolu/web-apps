# ============================================
# models.py - Database Helper Functions
# ============================================
# This file contains all functions that
# interact with the MySQL database.
# Each function handles one specific task.

from werkzeug.security import generate_password_hash, check_password_hash


# ============================================
# USER (CUSTOMER) FUNCTIONS
# ============================================

def get_all_users(mysql):
    """Fetch all registered customers from the database."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cur.fetchall()
    cur.close()
    return users


def get_user_by_id(mysql, user_id):
    """Get a single user by their ID."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return user


def get_user_by_email(mysql, email):
    """Find a user by email (used during login)."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    return user


def register_user(mysql, full_name, email, phone, password):
    """
    Register a new customer.
    The password is hashed before storing for security.
    """
    hashed_password = generate_password_hash(password)
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO users (full_name, email, phone, password) VALUES (%s, %s, %s, %s)",
        (full_name, email, phone, hashed_password)
    )
    mysql.connection.commit()
    cur.close()


def verify_user_password(stored_password, provided_password):
    """Check if the login password matches the stored hashed password."""
    return check_password_hash(stored_password, provided_password)


def delete_user(mysql, user_id):
    """Delete a user from the database (admin action)."""
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cur.close()


# ============================================
# ADMIN FUNCTIONS
# ============================================

def get_admin_by_username(mysql, username):
    """Find an admin by username (used during admin login)."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
    admin = cur.fetchone()
    cur.close()
    return admin


def create_default_admin(mysql):
    """
    Creates a default admin if none exists.
    Default credentials: admin / admin123
    Call this once when setting up the app.
    """
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
    """Fetch all cars from the database."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cars ORDER BY created_at DESC")
    cars = cur.fetchall()
    cur.close()
    return cars


def get_available_cars(mysql):
    """Fetch only cars that are currently available for rental."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cars WHERE status = 'available' ORDER BY price_per_day ASC")
    cars = cur.fetchall()
    cur.close()
    return cars


def get_car_by_id(mysql, car_id):
    """Get a single car by its ID."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cars WHERE id = %s", (car_id,))
    car = cur.fetchone()
    cur.close()
    return car


def add_car(mysql, name, brand, model, year, color, plate_number, category, seats, price_per_day, description):
    """Add a new car to the fleet (admin action)."""
    cur = mysql.connection.cursor()
    cur.execute(
        """INSERT INTO cars (name, brand, model, year, color, plate_number, category, seats, price_per_day, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (name, brand, model, year, color, plate_number, category, seats, price_per_day, description)
    )
    mysql.connection.commit()
    cur.close()


def update_car(mysql, car_id, name, brand, model, year, color, plate_number, category, seats, price_per_day, description, status):
    """Update an existing car's details (admin action)."""
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE cars SET name=%s, brand=%s, model=%s, year=%s, color=%s,
           plate_number=%s, category=%s, seats=%s, price_per_day=%s,
           description=%s, status=%s WHERE id=%s""",
        (name, brand, model, year, color, plate_number, category, seats, price_per_day, description, status, car_id)
    )
    mysql.connection.commit()
    cur.close()


def delete_car(mysql, car_id):
    """Remove a car from the fleet (admin action)."""
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM cars WHERE id = %s", (car_id,))
    mysql.connection.commit()
    cur.close()


def update_car_status(mysql, car_id, status):
    """Update a car's availability status."""
    cur = mysql.connection.cursor()
    cur.execute("UPDATE cars SET status = %s WHERE id = %s", (status, car_id))
    mysql.connection.commit()
    cur.close()


# ============================================
# BOOKING FUNCTIONS
# ============================================

def create_booking(mysql, user_id, car_id, pickup_date, return_date, total_days, total_price, pickup_location):
    """
    Create a new booking record.
    Also marks the car as 'rented' so others can't book it.
    """
    cur = mysql.connection.cursor()

    # Insert the booking record
    cur.execute(
        """INSERT INTO bookings (user_id, car_id, pickup_date, return_date, total_days, total_price, pickup_location)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (user_id, car_id, pickup_date, return_date, total_days, total_price, pickup_location)
    )

    # Mark the car as 'rented' so it's no longer available
    cur.execute("UPDATE cars SET status = 'rented' WHERE id = %s", (car_id,))

    mysql.connection.commit()
    cur.close()


def get_user_bookings(mysql, user_id):
    """
    Get all bookings for a specific customer.
    Joins the cars table to show car details.
    """
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
    """
    Fetch all bookings (admin view).
    Joins users and cars tables for complete info.
    """
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
    """
    Update the status of a booking (admin action).
    If completed or cancelled, make the car available again.
    """
    cur = mysql.connection.cursor()

    # Get the car_id for this booking first
    cur.execute("SELECT car_id FROM bookings WHERE id = %s", (booking_id,))
    booking = cur.fetchone()

    # Update the booking status
    cur.execute("UPDATE bookings SET status = %s WHERE id = %s", (status, booking_id))

    # If booking is done or cancelled, free up the car
    if status in ('completed', 'cancelled') and booking:
        cur.execute("UPDATE cars SET status = 'available' WHERE id = %s", (booking['car_id'],))

    mysql.connection.commit()
    cur.close()


def cancel_booking(mysql, booking_id, user_id):
    """Allow a customer to cancel their own booking."""
    cur = mysql.connection.cursor()

    # Make sure this booking belongs to this user
    cur.execute("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
    booking = cur.fetchone()

    if booking:
        cur.execute("UPDATE bookings SET status = 'cancelled' WHERE id = %s", (booking_id,))
        # Make the car available again
        cur.execute("UPDATE cars SET status = 'available' WHERE id = %s", (booking['car_id'],))
        mysql.connection.commit()

    cur.close()
    return booking is not None


# ============================================
# DASHBOARD / STATISTICS FUNCTIONS
# ============================================

def get_dashboard_stats(mysql):
    """
    Fetch key statistics for the admin dashboard.
    Returns counts of users, cars, bookings, and revenue.
    """
    cur = mysql.connection.cursor()

    # Total registered customers
    cur.execute("SELECT COUNT(*) as count FROM users")
    total_users = cur.fetchone()['count']

    # Total cars in fleet
    cur.execute("SELECT COUNT(*) as count FROM cars")
    total_cars = cur.fetchone()['count']

    # Cars currently available
    cur.execute("SELECT COUNT(*) as count FROM cars WHERE status = 'available'")
    available_cars = cur.fetchone()['count']

    # Total bookings ever made
    cur.execute("SELECT COUNT(*) as count FROM bookings")
    total_bookings = cur.fetchone()['count']

    # Active (confirmed or pending) bookings
    cur.execute("SELECT COUNT(*) as count FROM bookings WHERE status IN ('pending', 'confirmed')")
    active_bookings = cur.fetchone()['count']

    # Total revenue from completed bookings
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
