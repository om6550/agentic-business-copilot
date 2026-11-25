import sqlite3

DB_PATH = "data/business.db"


def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -------------------------
    # CUSTOMERS
    # -------------------------
    customers = [
        (
            "Rajesh Patel",
            "Patel Agriculture",
            "9876543210",
            "Ahmedabad",
            "Farmer",
            "Hydraulic Trailer",
            "active",
        ),
        (
            "Mahesh Solanki",
            "Solanki Farm Equipment",
            "9876501234",
            "Anand",
            "Dealer",
            "Heavy Duty Trailer",
            "active",
        ),
        (
            "Vijay Parmar",
            "Parmar Agro",
            "9898989898",
            "Khambhat",
            "Farmer",
            "Agriculture Trailer",
            "active",
        ),
        (
            "Kiran Shah",
            "Shah Transport",
            "9825012345",
            "Vadodara",
            "Transport Business",
            "Heavy Duty Trailer",
            "active",
        ),
        (
            "Ramesh Chaudhary",
            "Chaudhary Farms",
            "9912345678",
            "Nadiad",
            "Farmer",
            "Tractor Trailer",
            "active",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO customers
        (name, company, phone, city, customer_type,
         interested_product, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        customers,
    )

    # -------------------------
    # PRODUCTS
    # -------------------------
    products = [
        (
            "Standard Tractor Trailer",
            "Tractor Trailer",
            5.0,
            185000,
            "Standard agricultural tractor trailer suitable for farm transportation.",
            1,
        ),
        (
            "Hydraulic Trailer",
            "Hydraulic Trailer",
            8.0,
            275000,
            "Hydraulic tipping trailer designed for efficient agricultural material unloading.",
            1,
        ),
        (
            "Heavy Duty Trailer",
            "Heavy Duty",
            12.0,
            425000,
            "Heavy duty trailer for high-load agricultural and transport applications.",
            1,
        ),
        (
            "Agriculture Trailer Pro",
            "Agriculture",
            7.0,
            235000,
            "Premium agriculture trailer for farms and agricultural businesses.",
            1,
        ),
        (
            "Custom Trailer",
            "Customized",
            10.0,
            350000,
            "Custom-built trailer configurable according to customer requirements.",
            1,
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO products
        (product_name, category, capacity_tons, base_price,
         description, active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        products,
    )

    # -------------------------
    # LEADS
    # -------------------------
    leads = [
        (
            "Amit Patel",
            "9876112233",
            "Instagram",
            "Hydraulic Trailer",
            1,
            "new",
            "Interested in hydraulic tipping mechanism.",
        ),
        (
            "Suresh Patel",
            "9822334455",
            "Website",
            "Heavy Duty Trailer",
            2,
            "contacted",
            "Looking for two trailers for transport business.",
        ),
        (
            "Bhavesh Rana",
            "9900112233",
            "Referral",
            "Agriculture Trailer",
            1,
            "new",
            "Needs trailer for agricultural transportation.",
        ),
        (
            "Jignesh Patel",
            "9812345678",
            "WhatsApp",
            "Custom Trailer",
            1,
            "qualified",
            "Requested customized dimensions.",
        ),
        (
            "Deepak Shah",
            "9898123456",
            "Facebook",
            "Standard Tractor Trailer",
            1,
            "new",
            "Asked about current pricing and availability.",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO leads
        (customer_name, phone, source, interested_product,
         quantity, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        leads,
    )

    # -------------------------
    # INVENTORY
    # -------------------------
    inventory = [
        (1, 8, "Main Warehouse"),
        (2, 4, "Main Warehouse"),
        (3, 2, "Main Warehouse"),
        (4, 6, "Main Warehouse"),
        (5, 1, "Production Unit"),
    ]

    cursor.executemany(
        """
        INSERT INTO inventory
        (product_id, quantity_available, warehouse)
        VALUES (?, ?, ?)
        """,
        inventory,
    )

    # -------------------------
    # ORDERS
    # -------------------------
    orders = [
        (1, 2, 1, 370000, "confirmed", "in_production"),
        (2, 3, 1, 850000, "confirmed", "ready_for_dispatch"),
        (3, 2, 1, 275000, "pending", "not_started"),
    ]

    cursor.executemany(
        """
        INSERT INTO orders
        (customer_id, product_id, quantity, total_amount,
         order_status, delivery_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        orders,
    )

    conn.commit()
    conn.close()

    print("Synthetic business data inserted successfully.")


if __name__ == "__main__":
    seed_database()