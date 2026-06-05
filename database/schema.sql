CREATE DATABASE IF NOT EXISTS attendance_system
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE attendance_system;

-- Users table: stores registered individuals
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE,
    department  VARCHAR(100),
    role        ENUM('student', 'employee', 'admin') DEFAULT 'employee',
    face_encoding TEXT,
    image_path  VARCHAR(255),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Attendance table: stores attendance records
CREATE TABLE IF NOT EXISTS attendance (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    check_in    DATETIME NOT NULL,
    check_out   DATETIME,
    status      ENUM('present', 'late', 'absent') DEFAULT 'present',
    confidence  DECIMAL(5,2),
    image_path  VARCHAR(255),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, check_in),
    INDEX idx_date (check_in)
) ENGINE=InnoDB;

-- Attendance logs table: stores detailed recognition logs
CREATE TABLE IF NOT EXISTS attendance_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    event_type  ENUM('check_in', 'check_out', 'unknown_face', 'error') NOT NULL,
    confidence  DECIMAL(5,2),
    details     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;
