# ============================================
# routes.py - All Application Routes
# ============================================

from flask import render_template, request, redirect, url_for, session, flash
from datetime import datetime, date
from models import (
    get_user_by_email, register_user, verify_user_password,
    get_admin_by_username, create_default_admin,
    get_all_cars, get_available_cars, get_car_by_id,
    add_car, update_car, delete_car,
    create_booking, get_user_bookings, get_all_bookings,
    update_booking_status, cancel_booking,
    get_all_users, delete_user, get_dashboard_stats,
    get_user_by_id
)
from werkzeug.security import check_password_hash


def register_routes(app, mysql, ngn_rate=1550):
    """Register all routes with the Flask app."""

    def format_naira(usd_amount):
        return f"₦{float(usd_amount) * ngn_rate:,.2f}"

    # ============================================
    # HELPER: Login check decorators
    # ============================================

    def login_required(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to continue.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated

    def admin_required(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'admin_id' not in session:
                flash('Admin access required.', 'warning')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated

    # ============================================
    # PUBLIC ROUTES
    # ============================================

    @app.route('/')
    def index():
        cars = get_available_cars(mysql)
        return render_template('index.html', cars=cars)

    @app.route('/cars')
    def cars():
        category = request.args.get('category', '')
        all_cars = get_available_cars(mysql)
        if category:
            all_cars = [c for c in all_cars if c['category'] == category]
        return render_template('cars.html', cars=all_cars, selected_category=category)

    @app.route('/car/<int:car_id>')
    def car_detail(car_id):
        car = get_car_by_id(mysql, car_id)
        if not car:
            flash('Car not found.', 'danger')
            return redirect(url_for('cars'))
        return render_template('car_detail.html', car=car)

    # ============================================
    # AUTHENTICATION ROUTES
    # ============================================

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form['phone']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('register'))

            existing_user = get_user_by_email(mysql, email)
            if existing_user:
                flash('Email already registered. Please login.', 'danger')
                return redirect(url_for('register'))

            register_user(mysql, full_name, email, phone, password)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = get_user_by_email(mysql, email)

            if user and verify_user_password(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                flash(f"Welcome back, {user['full_name']}!", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        session.pop('user_name', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    # ============================================
    # CUSTOMER DASHBOARD ROUTES
    # ============================================

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = get_user_by_id(mysql, session['user_id'])
        bookings = get_user_bookings(mysql, session['user_id'])
        return render_template('dashboard.html', user=user, bookings=bookings)

    @app.route('/book/<int:car_id>', methods=['GET', 'POST'])
    @login_required
    def book_car(car_id):
        car = get_car_by_id(mysql, car_id)

        if not car:
            flash('Car not found.', 'danger')
            return redirect(url_for('cars'))

        if car['status'] != 'available':
            flash('This car is not available for booking.', 'warning')
            return redirect(url_for('cars'))

        if request.method == 'POST':
            pickup_date_str = request.form['pickup_date']
            return_date_str = request.form['return_date']
            pickup_location = request.form['pickup_location']

            pickup_date = datetime.strptime(pickup_date_str, '%Y-%m-%d').date()
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()

            if return_date <= pickup_date:
                flash('Return date must be after pickup date.', 'danger')
                return redirect(url_for('book_car', car_id=car_id))

            total_days = (return_date - pickup_date).days
            total_price = total_days * float(car['price_per_day'])

            create_booking(
                mysql,
                user_id=session['user_id'],
                car_id=car_id,
                pickup_date=pickup_date,
                return_date=return_date,
                total_days=total_days,
                total_price=total_price,
                pickup_location=pickup_location
            )

            flash(f'Booking confirmed! Total: {format_naira(total_price)} for {total_days} day(s).', 'success')
            return redirect(url_for('dashboard'))

        today = date.today().strftime('%Y-%m-%d')
        return render_template('booking.html', car=car, today=today)

    @app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
    @login_required
    def cancel_booking_route(booking_id):
        success = cancel_booking(mysql, booking_id, session['user_id'])
        if success:
            flash('Booking cancelled successfully.', 'success')
        else:
            flash('Unable to cancel booking.', 'danger')
        return redirect(url_for('dashboard'))

    # ============================================
    # ADMIN ROUTES
    # ============================================

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            create_default_admin(mysql)
            admin = get_admin_by_username(mysql, username)

            if admin and check_password_hash(admin['password'], password):
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['username']
                flash('Welcome, Admin!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials.', 'danger')

        return render_template('admin_login.html')

    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_id', None)
        session.pop('admin_name', None)
        flash('Admin logged out.', 'info')
        return redirect(url_for('admin_login'))

    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        stats = get_dashboard_stats(mysql)
        recent_bookings = get_all_bookings(mysql)[:5]
        return render_template('admin_dashboard.html', stats=stats, recent_bookings=recent_bookings)

    @app.route('/admin/cars')
    @admin_required
    def admin_cars():
        cars = get_all_cars(mysql)
        return render_template('admin_cars.html', cars=cars)

    @app.route('/admin/add_car', methods=['POST'])
    @admin_required
    def admin_add_car():
        add_car(
            mysql,
            name=request.form['name'],
            brand=request.form['brand'],
            model=request.form['model'],
            year=int(request.form['year']),
            color=request.form['color'],
            plate_number=request.form['plate_number'],
            category=request.form['category'],
            tier=request.form.get('tier', 'D'),
            seats=int(request.form['seats']),
            price_per_day=float(request.form['price_per_day']),
            description=request.form['description'],
            image_url=request.form.get('image_url') or None
        )
        flash('Car added successfully!', 'success')
        return redirect(url_for('admin_cars'))

    @app.route('/admin/edit_car/<int:car_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_car(car_id):
        car = get_car_by_id(mysql, car_id)

        if request.method == 'POST':
            update_car(
                mysql, car_id,
                name=request.form['name'],
                brand=request.form['brand'],
                model=request.form['model'],
                year=int(request.form['year']),
                color=request.form['color'],
                plate_number=request.form['plate_number'],
                category=request.form['category'],
                tier=request.form.get('tier', 'D'),
                seats=int(request.form['seats']),
                price_per_day=float(request.form['price_per_day']),
                description=request.form['description'],
                status=request.form['status'],
                image_url=request.form.get('image_url') or None
            )
            flash('Car updated successfully!', 'success')
            return redirect(url_for('admin_cars'))

        return render_template('admin_edit_car.html', car=car)

    @app.route('/admin/delete_car/<int:car_id>', methods=['POST'])
    @admin_required
    def admin_delete_car(car_id):
        delete_car(mysql, car_id)
        flash('Car deleted.', 'success')
        return redirect(url_for('admin_cars'))

    @app.route('/admin/bookings')
    @admin_required
    def admin_bookings():
        bookings = get_all_bookings(mysql)
        return render_template('admin_bookings.html', bookings=bookings)

    @app.route('/admin/update_booking/<int:booking_id>', methods=['POST'])
    @admin_required
    def admin_update_booking(booking_id):
        new_status = request.form['status']
        update_booking_status(mysql, booking_id, new_status)
        flash(f'Booking status updated to {new_status}.', 'success')
        return redirect(url_for('admin_bookings'))

    @app.route('/admin/users')
    @admin_required
    def admin_users():
        users = get_all_users(mysql)
        return render_template('admin_users.html', users=users)

    @app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
    @admin_required
    def admin_delete_user(user_id):
        delete_user(mysql, user_id)
        flash('User deleted.', 'success')
        return redirect(url_for('admin_users'))

    return app