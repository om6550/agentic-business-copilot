
import sqlite3
from pathlib import Path

# Database location
DB_PATH = Path(__file__).resolve().parent / "data" / "business.db"


def get_db_connection():
    """Connect to the existing business database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Business database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def find_product(product_name):
    """Find a product by its exact name."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                product_id,
                product_name,
                category,
                capacity_tons,
                base_price,
                description
            FROM products
            WHERE active = 1
              AND product_name = ? COLLATE NOCASE
            """,
            (product_name.strip(),)
        )

        product = cursor.fetchone()

        if product is None:
            return {
                "success": False,
                "message": f"Product not found: {product_name}"
            }

        return {
            "success": True,
            "product": dict(product)
        }

    finally:
        conn.close()


def check_inventory(product_name):
    """Check recorded stock for a product."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                p.product_name,
                i.quantity_available,
                i.warehouse
            FROM products AS p
            LEFT JOIN inventory AS i
                ON p.product_id = i.product_id
            WHERE p.active = 1
              AND p.product_name = ? COLLATE NOCASE
            """,
            (product_name.strip(),)
        )

        rows = cursor.fetchall()

        if not rows:
            return {
                "success": False,
                "message": f"Product not found: {product_name}"
            }

        inventory_records = []

        for row in rows:
            inventory_records.append({
                "product_name": row["product_name"],
                "quantity_available": row["quantity_available"],
                "warehouse": row["warehouse"]
            })

        return {
            "success": True,
            "inventory": inventory_records
        }

    finally:
        conn.close()


def find_customer(customer_name):
    """Find a customer by their exact name."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                customer_id,
                name,
                company,
                phone,
                city,
                customer_type,
                interested_product,
                status
            FROM customers
            WHERE name = ? COLLATE NOCASE
            """,
            (customer_name.strip(),)
        )

        customer = cursor.fetchone()

        if customer is None:
            return {
                "success": False,
                "message": f"Customer not found: {customer_name}"
            }

        return {
            "success": True,
            "customer": dict(customer)
        }

    finally:
        conn.close()


def add_customer(
    name,
    phone,
    company="",
    city="",
    customer_type="",
    interested_product=""
):
    """Register a new customer safely in SQLite."""

    # Validate customer name
    if not isinstance(name, str) or not name.strip():
        return {
            "success": False,
            "message": "Customer name is required."
        }

    # Validate phone number
    if not isinstance(phone, str):
        return {
            "success": False,
            "message": "A valid phone number is required."
        }

    phone = phone.strip()
    phone_digits = "".join(
        character for character in phone
        if character.isdigit()
    )

    if not 7 <= len(phone_digits) <= 15:
        return {
            "success": False,
            "message": "Enter a valid phone number containing 7 to 15 digits."
        }

    name = name.strip()
    company = company.strip() if isinstance(company, str) else ""
    city = city.strip() if isinstance(city, str) else ""
    customer_type = (
        customer_type.strip()
        if isinstance(customer_type, str) else ""
    )
    interested_product = (
        interested_product.strip()
        if isinstance(interested_product, str) else ""
    )

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Prevent duplicate registration during concurrent requests.
        conn.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT customer_id, name, phone
            FROM customers
            WHERE phone IS NOT NULL
              AND TRIM(phone) != ''
        """)

        existing_customers = cursor.fetchall()

        for existing in existing_customers:
            existing_digits = "".join(
                character for character in existing["phone"]
                if character.isdigit()
            )

            if existing_digits == phone_digits:
                conn.rollback()
                return {
                    "success": False,
                    "message": (
                        f"Phone number already belongs to "
                        f"{existing['name']} "
                        f"(Customer ID: {existing['customer_id']})."
                    )
                }

        cursor.execute("""
            INSERT INTO customers (
                name,
                company,
                phone,
                city,
                customer_type,
                interested_product,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        """, (
            name,
            company or None,
            phone,
            city or None,
            customer_type or None,
            interested_product or None
        ))

        customer_id = cursor.lastrowid
        conn.commit()

        return {
            "success": True,
            "message": "Customer registered successfully.",
            "customer": {
                "customer_id": customer_id,
                "name": name,
                "company": company or None,
                "phone": phone,
                "city": city or None,
                "customer_type": customer_type or None,
                "interested_product": interested_product or None,
                "status": "active"
            }
        }

    except sqlite3.Error as error:
        conn.rollback()
        return {
            "success": False,
            "message": f"Could not register customer: {error}"
        }

    finally:
        conn.close()


def find_order(order_id):
    """Find an order with its customer and product details."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                o.order_id,
                c.name AS customer_name,
                p.product_name,
                o.quantity,
                o.total_amount,
                o.order_status,
                o.delivery_status
            FROM orders AS o
            JOIN customers AS c
                ON o.customer_id = c.customer_id
            JOIN products AS p
                ON o.product_id = p.product_id
            WHERE o.order_id = ?
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if order is None:
            return {
                "success": False,
                "message": f"Order not found: {order_id}"
            }

        return {
            "success": True,
            "order": dict(order)
        }

    finally:
        conn.close()


def get_business_analytics():
    """Return business analytics calculated from SQLite records."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Customer and product overview
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM customers) AS total_customers,
                (SELECT COUNT(*) FROM products WHERE active = 1)
                    AS active_products
        """)
        overview = dict(cursor.fetchone())

        # Inventory overview
        cursor.execute("""
            SELECT
                COALESCE(SUM(stock.total_quantity), 0)
                    AS total_inventory_units,

                SUM(CASE
                    WHEN stock.record_count > 0
                     AND stock.total_quantity <= 0 THEN 1
                    ELSE 0
                END) AS out_of_stock_products,

                SUM(CASE
                    WHEN stock.record_count IS NULL THEN 1
                    ELSE 0
                END) AS products_without_stock_records

            FROM products AS p

            LEFT JOIN (
                SELECT
                    product_id,
                    COUNT(*) AS record_count,
                    SUM(COALESCE(quantity_available, 0))
                        AS total_quantity
                FROM inventory
                GROUP BY product_id
            ) AS stock
                ON p.product_id = stock.product_id

            WHERE p.active = 1
        """)
        inventory = dict(cursor.fetchone())

        # Order and recorded order value overview
        cursor.execute("""
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM(total_amount), 0)
                    AS total_recorded_order_value
            FROM orders
        """)
        order_summary = dict(cursor.fetchone())

        # Order status breakdown
        cursor.execute("""
            SELECT
                order_status,
                COUNT(*) AS order_count
            FROM orders
            GROUP BY order_status
            ORDER BY order_count DESC
        """)
        order_status = [
            dict(row) for row in cursor.fetchall()
        ]

        # Top products by ordered quantity
        cursor.execute("""
            SELECT
                p.product_name,
                SUM(o.quantity) AS total_quantity_ordered,
                COUNT(o.order_id) AS total_orders,
                COALESCE(SUM(o.total_amount), 0)
                    AS recorded_order_value
            FROM orders AS o
            JOIN products AS p
                ON o.product_id = p.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY total_quantity_ordered DESC
            LIMIT 5
        """)
        top_products = [
            dict(row) for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "overview": overview,
            "inventory": inventory,
            "orders": order_summary,
            "order_status": order_status,
            "top_products": top_products,
        }

    except Exception as error:
        return {
            "success": False,
            "message": str(error)
        }

    finally:
        conn.close()


def get_quotation_analytics():
    """Calculate quotation analytics from SQLite."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_quotations,

                SUM(CASE WHEN status = 'approved'
                    THEN 1 ELSE 0 END) AS approved,

                SUM(CASE WHEN status = 'draft'
                    THEN 1 ELSE 0 END) AS draft,

                SUM(CASE WHEN status = 'rejected'
                    THEN 1 ELSE 0 END) AS rejected,

                COALESCE(SUM(
                    CASE WHEN status = 'approved'
                    THEN subtotal ELSE 0 END
                ), 0) AS approved_quotation_value

            FROM quotations
        """)

        summary = dict(cursor.fetchone())

        cursor.execute("""
            SELECT
                p.product_name,
                SUM(q.quantity) AS total_quantity,
                COUNT(q.quotation_id) AS quotation_count,
                SUM(q.subtotal) AS quotation_value
            FROM quotations AS q
            JOIN products AS p
                ON q.product_id = p.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY quotation_count DESC
        """)

        products = [
            dict(row) for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "summary": summary,
            "products": products,
        }

    except Exception as error:
        return {
            "success": False,
            "message": str(error)
        }

    finally:
        conn.close()

def get_product_analysis(product_names=None, order_by=None):
    """Compare products or find cheapest/most expensive products."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        query = """
            SELECT product_id, product_name, category,
                   capacity_tons, base_price, description
            FROM products
            WHERE active = 1
        """
        params = []

        if product_names:
            placeholders = ",".join("?" for _ in product_names)
            query += f" AND product_name IN ({placeholders}) COLLATE NOCASE"
            params.extend(product_names)

        if order_by == "cheapest":
            query += " ORDER BY base_price ASC"
        elif order_by == "expensive":
            query += " ORDER BY base_price DESC"
        else:
            query += " ORDER BY product_name"

        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]

        if product_names and len(products) != len(product_names):
            found = {p["product_name"].lower() for p in products}
            missing = [
                name for name in product_names
                if name.lower() not in found
            ]
            return {
                "success": False,
                "message": "Product not found: " + ", ".join(missing)
            }

        return {"success": True, "products": products}

    except Exception as error:
        return {"success": False, "message": str(error)}
    finally:
        conn.close()


def get_all_inventory():
    """Return stock information for every active product."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.product_name,
                COUNT(i.inventory_id) AS stock_records,
                SUM(i.quantity_available) AS total_quantity,
                GROUP_CONCAT(DISTINCT i.warehouse) AS warehouses
            FROM products AS p
            LEFT JOIN inventory AS i
                ON p.product_id = i.product_id
            WHERE p.active = 1
            GROUP BY p.product_id, p.product_name
            ORDER BY p.product_name
        """)

        return {
            "success": True,
            "inventory": [dict(row) for row in cursor.fetchall()]
        }

    except Exception as error:
        return {"success": False, "message": str(error)}
    finally:
        conn.close()


def get_inventory_summary():
    """Return total stock, out-of-stock products and missing stock records."""
    conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(SUM(stock.total_quantity), 0)
                    AS total_inventory_units,
                SUM(CASE
                    WHEN stock.record_count > 0
                     AND stock.total_quantity <= 0 THEN 1
                    ELSE 0
                END) AS out_of_stock_products,
                SUM(CASE
                    WHEN stock.record_count IS NULL THEN 1
                    ELSE 0
                END) AS products_without_stock_records
            FROM products AS p
            LEFT JOIN (
                SELECT
                    product_id,
                    COUNT(*) AS record_count,
                    SUM(COALESCE(quantity_available, 0))
                        AS total_quantity
                FROM inventory
                GROUP BY product_id
            ) AS stock
                ON p.product_id = stock.product_id
            WHERE p.active = 1
        """)

        return {
            "success": True,
            "summary": dict(cursor.fetchone())
        }

    except Exception as error:
        return {"success": False, "message": str(error)}
    finally:
        conn.close()



def get_customers(status=None, search=None):
    """List customers with optional status and search filters."""

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        query = """
            SELECT
                customer_id,
                name,
                company,
                phone,
                city,
                customer_type,
                interested_product,
                status
            FROM customers
        """

        conditions = []
        params = []

        if status:
            conditions.append("status = ? COLLATE NOCASE")
            params.append(status)

        if search and search.strip():
            conditions.append(
                "(name LIKE ? COLLATE NOCASE "
                "OR phone LIKE ? COLLATE NOCASE "
                "OR company LIKE ? COLLATE NOCASE)"
            )

            search_value = f"%{search.strip()}%"
            params.extend([
                search_value,
                search_value,
                search_value
            ])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY name"

        cursor.execute(query, params)

        customers = [
            dict(row) for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "customers": customers,
            "count": len(customers)
        }

    except sqlite3.Error as error:
        return {
            "success": False,
            "message": str(error)
        }

    finally:
        conn.close()


def get_customer_profile(customer_id):
    """Return one customer's complete profile."""
    
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                customer_id,
                name,
                company,
                phone,
                city,
                customer_type,
                interested_product,
                status
            FROM customers
            WHERE customer_id = ?
        """, (customer_id,))

        customer = cursor.fetchone()

        if customer is None:
            return {
                "success": False,
                "not_found": True,
                "message": f"Customer not found: {customer_id}"
            }

        return {
            "success": True,
            "customer": dict(customer)
        }

    except sqlite3.Error as error:
        return {
            "success": False,
            "message": f"Could not retrieve customer profile: {error}"
        }

    finally:
        conn.close()


def get_customer_quotation_history(customer_id):
    """Return all quotations belonging to one customer."""

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # First, verify that the customer exists.
        cursor.execute("""
            SELECT customer_id, name
            FROM customers
            WHERE customer_id = ?
        """, (customer_id,))

        customer = cursor.fetchone()

        if customer is None:
            return {
                "success": False,
                "not_found": True,
                "message": f"Customer not found: {customer_id}"
            }

        # Retrieve only this customer's quotations.
        cursor.execute("""
            SELECT
                q.quotation_id,
                q.customer_id,
                p.product_name,
                q.quantity,
                q.unit_price,
                q.subtotal,
                q.status,
                q.inventory_checked,
                q.created_at,
                q.reviewed_at
            FROM quotations AS q
            JOIN products AS p
                ON q.product_id = p.product_id
            WHERE q.customer_id = ?
            ORDER BY
                q.created_at DESC,
                q.quotation_id DESC
        """, (customer_id,))

        quotations = [
            dict(row) for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "customer": {
                "customer_id": customer["customer_id"],
                "name": customer["name"]
            },
            "quotations": quotations,
            "count": len(quotations)
        }

    except sqlite3.Error as error:
        return {
            "success": False,
            "message": f"Could not retrieve quotation history: {error}"
        }

    finally:
        conn.close()



if __name__ == "__main__":
    
    print("\n--- PRODUCT LOOKUP TEST ---")
    print(find_product("Hydraulic Trailer"))

    print("\n--- INVENTORY CHECK TEST ---")
    print(check_inventory("Hydraulic Trailer"))

    print("\n--- CUSTOMER LOOKUP TEST ---")
    print(find_customer("Rajesh Patel"))

    print("\n--- ORDER LOOKUP TEST ---")
    print(find_order(1))

    print("\n--- UNKNOWN PRODUCT TEST ---")
    print(find_product("Unknown Trailer"))

    print("\n--- UNKNOWN CUSTOMER TEST ---")
    print(find_customer("Unknown Customer"))

    print("\n--- UNKNOWN ORDER TEST ---")
    print(find_order(9999))
