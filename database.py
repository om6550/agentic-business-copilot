import sqlite3
from pathlib import Path

# Database location
DB_PATH = Path(__file__).resolve().parent / "data" / "business.db"

def get_connection():
    """Create and return a SQLite database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_tables():
    """Create the initial business database tables."""

    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------
    # Customers
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            city TEXT,
            customer_type TEXT,
            interested_product TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    # -------------------------
    # Leads
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT,
            source TEXT,
            interested_product TEXT,
            quantity INTEGER,
            status TEXT DEFAULT 'new',
            notes TEXT
        )
    """)

    # -------------------------
    # Products
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT,
            capacity_tons REAL,
            base_price REAL,
            description TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    # -------------------------
    # Inventory
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity_available INTEGER DEFAULT 0,
            warehouse TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # -------------------------
    # Orders
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_amount REAL,
            order_status TEXT DEFAULT 'pending',
            delivery_status TEXT DEFAULT 'not_started',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    
    # -------------------------
    # Quotations
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotations (
            quotation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            subtotal REAL NOT NULL CHECK (subtotal >= 0),
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'approved', 'rejected')),
            inventory_checked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # -------------------------
    # Approval History
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approval_history (
            approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            quotation_id INTEGER NOT NULL,
            decision TEXT NOT NULL
                CHECK (decision IN ('approved', 'rejected')),
            reviewer TEXT NOT NULL,
            notes TEXT,
            reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quotation_id)
                REFERENCES quotations(quotation_id)
        )
    """)


    conn.commit()
    conn.close()

    print("Database tables created successfully.")
    print(f"Database location: {DB_PATH}")


if __name__ == "__main__":
    create_tables()