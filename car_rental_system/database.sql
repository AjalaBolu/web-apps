-- ============================================
-- ONLINE CAR RENTAL SYSTEM - Database Schema
-- ============================================

CREATE DATABASE IF NOT EXISTS car_rental_db;
USE car_rental_db;

-- ----------------------------------------
-- TABLE: users (Customers who rent cars)
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,         -- Stored as hashed password
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------
-- TABLE: admins (System administrators)
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,         -- Stored as hashed password
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------
-- TABLE: cars (All available rental cars)
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,             -- e.g. "Toyota Camry"
    brand VARCHAR(50) NOT NULL,             -- e.g. "Toyota"
    model VARCHAR(50) NOT NULL,             -- e.g. "Camry"
    year INT NOT NULL,                      -- e.g. 2022
    color VARCHAR(30),
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    category VARCHAR(30),                   -- e.g. "Sedan", "SUV", "Truck"
    seats INT DEFAULT 5,
    price_per_day DECIMAL(10,2) NOT NULL,   -- Daily rental rate
    image_url VARCHAR(255),                 -- Path to car image
    status ENUM('available', 'rented', 'maintenance') DEFAULT 'available',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------
-- TABLE: bookings (All rental transactions)
-- Relationships:
--   - bookings.user_id  → users.id
--   - bookings.car_id   → cars.id
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    car_id INT NOT NULL,
    pickup_date DATE NOT NULL,
    return_date DATE NOT NULL,
    total_days INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'confirmed', 'cancelled', 'completed') DEFAULT 'pending',
    pickup_location VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
);

-- ----------------------------------------
-- SEED DATA: Default admin account
-- Password: admin123 (hashed below)
-- ----------------------------------------
INSERT INTO admins (username, password) VALUES (
    'admin',
    'pbkdf2:sha256:600000$salt$hashed'  -- Will be replaced by app on first run
);

-- ----------------------------------------
-- SEED DATA: Sample cars
-- ----------------------------------------
INSERT INTO cars (name, brand, model, year, color, plate_number, category, seats, price_per_day, description, status) VALUES
('Toyota Camry 2022', 'Toyota', 'Camry', 2022, 'White', 'ABC-1234', 'Sedan', 5, 45.00, 'Comfortable midsize sedan perfect for city and highway driving.', 'available'),
('Ford Explorer 2021', 'Ford', 'Explorer', 2021, 'Black', 'DEF-5678', 'SUV', 7, 75.00, 'Spacious SUV ideal for family trips and off-road adventures.', 'available'),
('Honda Civic 2023', 'Honda', 'Civic', 2023, 'Blue', 'GHI-9012', 'Sedan', 5, 40.00, 'Fuel-efficient compact sedan with modern features.', 'available'),
('Mercedes C-Class 2022', 'Mercedes', 'C-Class', 2022, 'Silver', 'JKL-3456', 'Luxury', 5, 120.00, 'Premium luxury sedan with top-of-the-line comfort and performance.', 'available'),
('Toyota HiLux 2021', 'Toyota', 'HiLux', 2021, 'Red', 'MNO-7890', 'Pickup', 5, 65.00, 'Rugged pickup truck suitable for heavy loads and rough terrain.', 'available'),
('Hyundai Tucson 2022', 'Hyundai', 'Tucson', 2022, 'Grey', 'PQR-1234', 'SUV', 5, 60.00, 'Stylish compact SUV with excellent fuel economy.', 'available');
