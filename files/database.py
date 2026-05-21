import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE = "foodie.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_attempts INTEGER DEFAULT 0,
            is_locked BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS auth_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            username TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id TEXT NOT NULL UNIQUE,
            restaurant TEXT,
            total REAL NOT NULL,
            cancelled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            emoji TEXT,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized.")


def create_user(username, email, password_hash, role="user"):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_last_login(user_id):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET last_login = ?, failed_attempts = 0 WHERE id = ?",
            (datetime.utcnow(), user_id),
        )
        conn.commit()
    finally:
        conn.close()


def increment_failed_attempts(username):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE username = ?",
            (username,),
        )
        conn.commit()
        row = conn.execute(
            "SELECT failed_attempts FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row and row["failed_attempts"] >= 5:
            lock_account(username)
            return True  # locked
        return False
    finally:
        conn.close()


def lock_account(username):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET is_locked = TRUE WHERE username = ?", (username,)
        )
        conn.commit()
    finally:
        conn.close()


def log_auth_event(event, username=None, ip_address=None, details=None):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO auth_logs (event, username, ip_address, details) VALUES (?, ?, ?, ?)",
            (event, username, ip_address, details),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_users():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, username, email, role, created_at, last_login, failed_attempts, is_locked FROM users"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_auth_logs(limit=100):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM auth_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_order(user_id, order_id, items, restaurant, total, cancelled=0):
    """Save an order to the database"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        # Insert order
        cursor.execute(
            """INSERT INTO orders (user_id, order_id, restaurant, total, cancelled)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, order_id, restaurant, total, cancelled),
        )
        order_db_id = cursor.lastrowid
        
        # Insert order items
        for item in items:
            cursor.execute(
                """INSERT INTO order_items (order_id, item_name, emoji, price, quantity)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_db_id, item.get('name'), item.get('emoji'), item.get('price'), item.get('qty')),
            )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving order: {e}")
        return False
    finally:
        conn.close()


def get_user_orders(user_id):
    """Fetch all orders for a specific user"""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT o.id, o.order_id, o.restaurant, o.total, o.cancelled, o.created_at
               FROM orders o
               WHERE o.user_id = ?
               ORDER BY o.created_at DESC""",
            (user_id,),
        ).fetchall()
        
        orders = []
        for row in rows:
            order_dict = dict(row)
            # Get items for this order
            items_rows = conn.execute(
                """SELECT item_name as name, emoji, price, quantity as qty
                   FROM order_items
                   WHERE order_id = ?""",
                (row['id'],),
            ).fetchall()
            order_dict['items'] = [dict(i) for i in items_rows]
            orders.append(order_dict)
        
        return orders
    finally:
        conn.close()


def delete_order(order_db_id, user_id):
    """Delete an order (only if it belongs to the user)"""
    conn = get_db()
    try:
        # Verify the order belongs to this user
        row = conn.execute(
            "SELECT user_id FROM orders WHERE id = ?", (order_db_id,)
        ).fetchone()
        
        if row and row['user_id'] == user_id:
            conn.execute("DELETE FROM orders WHERE id = ?", (order_db_id,))
            conn.commit()
            return True
        return False
    finally:
        conn.close()
