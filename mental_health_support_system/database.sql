-- ============================================================
-- ONLINE THERAPY AND MENTAL HEALTH SUPPORT SYSTEM
-- MySQL Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS mental_health_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mental_health_db;

-- ------------------------------------------------------------
-- TABLE: admins
-- System administrators who manage the platform
-- ------------------------------------------------------------
CREATE TABLE admins (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(80)  NOT NULL UNIQUE,
    email       VARCHAR(120) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE: users
-- Registered patients / general users
-- ------------------------------------------------------------
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(80)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    full_name       VARCHAR(150),
    phone           VARCHAR(20),
    date_of_birth   DATE,
    gender          ENUM('male','female','other','prefer_not_to_say'),
    profile_picture VARCHAR(255) DEFAULT 'default.png',
    bio             TEXT,
    is_active       BOOLEAN      DEFAULT TRUE,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE: therapists
-- Mental health professionals registered on the platform
-- ------------------------------------------------------------
CREATE TABLE therapists (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NOT NULL,          -- links to users table
    specialization  VARCHAR(150),
    license_number  VARCHAR(100),
    years_experience INT         DEFAULT 0,
    education       TEXT,
    bio             TEXT,
    consultation_fee DECIMAL(10,2) DEFAULT 0.00,
    is_approved     BOOLEAN      DEFAULT FALSE,     -- admin must approve
    is_available    BOOLEAN      DEFAULT TRUE,
    rating          DECIMAL(3,2) DEFAULT 0.00,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE: appointments
-- Therapy session bookings
-- ------------------------------------------------------------
CREATE TABLE appointments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NOT NULL,
    therapist_id    INT          NOT NULL,
    appointment_date DATE        NOT NULL,
    appointment_time TIME        NOT NULL,
    duration_minutes INT         DEFAULT 60,
    session_type    ENUM('online','in-person') DEFAULT 'online',
    status          ENUM('pending','confirmed','completed','cancelled') DEFAULT 'pending',
    notes           TEXT,
    meeting_link    VARCHAR(255),
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (therapist_id) REFERENCES therapists(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE: messages
-- User-to-therapist secure messaging
-- ------------------------------------------------------------
CREATE TABLE messages (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    sender_id   INT          NOT NULL,
    receiver_id INT          NOT NULL,
    content     TEXT         NOT NULL,
    is_read     BOOLEAN      DEFAULT FALSE,
    sent_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id)   REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE: mood_logs
-- Daily mood tracking entries
-- ------------------------------------------------------------
CREATE TABLE mood_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    mood_score  TINYINT      NOT NULL CHECK (mood_score BETWEEN 1 AND 5),
    mood_label  VARCHAR(50),            -- e.g., 'Happy', 'Sad', 'Anxious'
    mood_emoji  VARCHAR(10),            -- stores emoji character
    notes       TEXT,
    logged_date DATE         NOT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE: journal_entries
-- Personal mental wellness journal
-- ------------------------------------------------------------
CREATE TABLE journal_entries (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    title       VARCHAR(200),
    content     TEXT         NOT NULL,
    mood_score  TINYINT,
    is_private  BOOLEAN      DEFAULT TRUE,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE: resources
-- Mental health articles, guides, and tips
-- ------------------------------------------------------------
CREATE TABLE resources (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    admin_id    INT          NOT NULL,
    title       VARCHAR(200) NOT NULL,
    content     TEXT         NOT NULL,
    category    ENUM('article','self-help','wellness','motivational','guide') DEFAULT 'article',
    image_url   VARCHAR(255),
    is_published BOOLEAN     DEFAULT TRUE,
    views       INT          DEFAULT 0,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- SEED DATA: Default admin account
-- Password: Admin@1234 (hashed with bcrypt in app)
-- ------------------------------------------------------------
INSERT INTO admins (username, email, password) VALUES
('admin', 'admin@mentalhealth.com', 'HASH_PLACEHOLDER');

-- ============================================================
-- END OF SCHEMA
-- ============================================================
