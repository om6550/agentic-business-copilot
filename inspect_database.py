import sqlite3
from pathlib import Path

DB_PATH = Path("data/business.db")

def inspect_database():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tables = ["customers", "leads", "products", "inventory", "orders"]

    for table in tables:
        print(f"\n{'=' * 50}")
        print(f"TABLE: {table.upper()}")
        print("=" * 50)

        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        if not columns:
            print("Table does not exist.")
            continue

        print("Columns:", ", ".join(row["name"] for row in columns))

        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Total records: {count}")

        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()

        for row in rows:
            print(dict(row))

        if not rows:
            print("No records found.")

    conn.close()

if __name__ == "__main__":
    inspect_database()
