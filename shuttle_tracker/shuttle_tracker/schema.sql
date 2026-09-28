PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student','driver','admin'))
);

CREATE TABLE IF NOT EXISTS shuttles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shuttle_number TEXT NOT NULL UNIQUE,
    driver_id INTEGER REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'offline' CHECK (status IN ('active','offline'))
);

CREATE TABLE IF NOT EXISTS stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS route_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    stop_id INTEGER NOT NULL REFERENCES stops(id),
    sequence INTEGER NOT NULL,
    UNIQUE (route_id, sequence)
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shuttle_id INTEGER NOT NULL REFERENCES shuttles(id) ON DELETE CASCADE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_locations_shuttle ON locations (shuttle_id, id DESC);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shuttle_id INTEGER NOT NULL REFERENCES shuttles(id) ON DELETE CASCADE,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    start_time TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    end_time TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','completed'))
);
