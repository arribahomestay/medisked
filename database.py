import sqlite3
from datetime import datetime

DB_NAME = "database.db"


def init_db(db_path: str = DB_NAME) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )

     
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

     
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            role TEXT,
            action TEXT NOT NULL,
            details TEXT
        )
        """
    )

    
    try:
        cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    except sqlite3.OperationalError:
        
        pass

    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            schedule TEXT NOT NULL,
            notes TEXT,
            is_rescheduled INTEGER NOT NULL DEFAULT 0,
            barcode TEXT,
            is_paid INTEGER NOT NULL DEFAULT 0,
            amount_paid REAL
        )
        """
    )

    
    try:
        cur.execute("ALTER TABLE appointments ADD COLUMN is_rescheduled INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        
        pass
    try:
        cur.execute("ALTER TABLE appointments ADD COLUMN barcode TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE appointments ADD COLUMN is_paid INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE appointments ADD COLUMN amount_paid REAL")
    except sqlite3.OperationalError:
        pass

    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT
        )
        """
    )

    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS doctor_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            is_available INTEGER NOT NULL DEFAULT 1,
            max_appointments INTEGER,
            slot_length_minutes INTEGER,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
        """
    )

    
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        ("admin", "admin123", "admin"),
    )

    
    cur.execute(
        "INSERT OR IGNORE INTO system_settings (key, value) VALUES ('activity_logging_enabled', '1')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO system_settings (key, value) VALUES ('show_login_success_popup', '1')"
    )

    
    cur.execute(
        "DELETE FROM doctors WHERE name = ? AND notes = ?",
        ("Dr. Smith", "Sample doctor"),
    )

    
    cur.execute(
        "DELETE FROM appointments WHERE schedule IN (?,?,?)",
        (
            "2025-11-25 09:00",
            "2025-11-25 10:30",
            "2025-11-26 14:00",
        ),
    )

    conn.commit()
    conn.close()


def get_setting(key: str, default: str | None = None, db_path: str = DB_NAME) -> str | None:
    """Read a system setting from the database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row is not None else default
    finally:
        conn.close()


def set_setting(key: str, value: str, db_path: str = DB_NAME) -> None:
    """Persist a system setting in the database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO system_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()


def log_activity(username: str | None, role: str | None, action: str, details: str | None = None) -> None:
    """Insert a new activity log entry if logging is enabled.

    Timestamps are stored as 'YYYY-MM-DD hh:mm:ss AM/PM'.
    """
    
    try:
        enabled = get_setting("activity_logging_enabled", "1")
    except Exception:
        enabled = "1"
    if enabled != "1":
        return

    ts = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO activity_logs (timestamp, username, role, action, details) VALUES (?, ?, ?, ?, ?)",
            (ts, username, role, action, details),
        )
        conn.commit()
    finally:
        conn.close()


def get_activity_logs(limit: int = 200, db_path: str = DB_NAME):
    """Return the most recent activity log rows (timestamp, username, role, action, details)."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT timestamp, username, role, action, details FROM activity_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()
    finally:
        conn.close()
