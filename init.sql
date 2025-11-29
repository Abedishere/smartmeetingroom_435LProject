-- =====================================================
-- Meeting Room Booking System - Database Schema
-- =====================================================
-- This script initializes the PostgreSQL database schema
-- for the Smart Meeting Room Management System.
--
-- Author: Abdel Rahman El Kouche
-- Project: 435LProject - Meeting Room Booking System
-- Database: PostgreSQL 15
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- USERS TABLE
-- =====================================================
-- Stores user accounts with authentication and authorization
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'regular_user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Add comment to table
COMMENT ON TABLE users IS 'System users with authentication and role-based access control';
COMMENT ON COLUMN users.role IS 'User role: admin, regular_user, facility_manager, moderator, auditor, service_account';

-- =====================================================
-- ROOMS TABLE
-- =====================================================
-- Stores meeting room inventory with equipment details
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    equipment TEXT,
    location VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_rooms_name ON rooms(name);
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);
CREATE INDEX IF NOT EXISTS idx_rooms_capacity ON rooms(capacity);
CREATE INDEX IF NOT EXISTS idx_rooms_location ON rooms(location);

-- Add comments
COMMENT ON TABLE rooms IS 'Meeting rooms with capacity, equipment, and availability status';
COMMENT ON COLUMN rooms.equipment IS 'Comma-separated list of available equipment';
COMMENT ON COLUMN rooms.status IS 'Room status: available, booked, out_of_service';

-- =====================================================
-- BOOKINGS TABLE
-- =====================================================
-- Stores room reservations with conflict prevention
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraints
    CONSTRAINT fk_booking_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_room FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,

    -- Business logic constraints
    CONSTRAINT chk_booking_time CHECK (end_time > start_time),
    CONSTRAINT uq_booking_room_time_window UNIQUE (room_id, start_time, end_time)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_room_id ON bookings(room_id);
CREATE INDEX IF NOT EXISTS idx_bookings_start_time ON bookings(start_time);
CREATE INDEX IF NOT EXISTS idx_bookings_end_time ON bookings(end_time);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

-- Add comments
COMMENT ON TABLE bookings IS 'Room reservations with time slots and conflict detection';
COMMENT ON COLUMN bookings.status IS 'Booking status: confirmed, cancelled, completed';
COMMENT ON CONSTRAINT chk_booking_time ON bookings IS 'Ensures end time is after start time';
COMMENT ON CONSTRAINT uq_booking_room_time_window ON bookings IS 'Prevents double-booking of rooms';

-- =====================================================
-- REVIEWS TABLE
-- =====================================================
-- Stores room reviews with ratings and moderation
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT NOT NULL,
    flagged BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraints
    CONSTRAINT fk_review_room FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_reviews_room_id ON reviews(room_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_flagged ON reviews(flagged);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at);

-- Add comments
COMMENT ON TABLE reviews IS 'User reviews for meeting rooms with 5-star rating system';
COMMENT ON COLUMN reviews.rating IS 'Rating from 1 to 5 stars';
COMMENT ON COLUMN reviews.flagged IS 'Indicates if review is flagged for moderation';

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for rooms table
DROP TRIGGER IF EXISTS update_rooms_updated_at ON rooms;
CREATE TRIGGER update_rooms_updated_at
    BEFORE UPDATE ON rooms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA (Optional - for development/testing)
-- =====================================================

-- Insert default admin user (password: admin123)
-- Password hash generated with bcrypt, salt rounds: 12
INSERT INTO users (name, username, password_hash, email, role)
VALUES (
    'System Administrator',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIeWEHaSuu',
    'admin@meetingroom.local',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Insert facility manager (password: manager123)
INSERT INTO users (name, username, password_hash, email, role)
VALUES (
    'Facility Manager',
    'facility_manager',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p91IpW4pAYD4VppC4y7GGh9e',
    'manager@meetingroom.local',
    'facility_manager'
) ON CONFLICT (username) DO NOTHING;

-- Insert sample rooms
INSERT INTO rooms (name, capacity, equipment, location, status)
VALUES
    ('Conference Room A', 20, 'Projector, Whiteboard, Video Conferencing', 'Building A - Floor 1', 'available'),
    ('Meeting Room B', 10, 'TV Screen, Whiteboard', 'Building A - Floor 2', 'available'),
    ('Executive Boardroom', 15, 'Projector, Video Conferencing, Conference Phone', 'Building B - Floor 3', 'available'),
    ('Training Room', 30, 'Projector, Whiteboard, Sound System', 'Building C - Floor 1', 'available'),
    ('Small Meeting Room', 6, 'TV Screen', 'Building A - Floor 1', 'available')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Grant appropriate permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check table creation
-- SELECT table_name, table_type
-- FROM information_schema.tables
-- WHERE table_schema = 'public'
-- ORDER BY table_name;

-- Check indexes
-- SELECT tablename, indexname, indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
-- ORDER BY tablename, indexname;

-- Verify row counts
-- SELECT
--     (SELECT COUNT(*) FROM users) as users_count,
--     (SELECT COUNT(*) FROM rooms) as rooms_count,
--     (SELECT COUNT(*) FROM bookings) as bookings_count,
--     (SELECT COUNT(*) FROM reviews) as reviews_count;

-- =====================================================
-- END OF SCHEMA
-- =====================================================