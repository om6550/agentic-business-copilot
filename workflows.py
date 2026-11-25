
import sqlite3
from pathlib import Path

from tools import find_product, check_inventory, find_customer


def get_workflow_db_connection():
    """Connect to the project's existing business database."""
    db_path = Path(__file__).resolve().parent / "data" / "business.db"
    return sqlite3.connect(db_path)


def prepare_quotation_draft(customer_name, product_name, quantity):
    """Prepare and save a quotation draft for human review."""

    # Step 1: Validate quantity.
    try:
        quantity_text = str(quantity).strip()

        if not quantity_text.isdigit():
            raise ValueError

        quantity = int(quantity_text)

        if quantity <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Quantity must be a positive whole number.",
        }

    # Step 2: Find the customer.
    customer_result = find_customer(customer_name)

    if not customer_result.get("success"):
        return {
            "success": False,
            "message": (
                f"Customer '{customer_name}' was not found. "
                "Please check the customer name."
            ),
        }

    customer = customer_result["customer"]

    # Step 3: Find the product.
    product_result = find_product(product_name)

    if not product_result.get("success"):
        return {
            "success": False,
            "message": (
                f"Product '{product_name}' was not found. "
                "Please check the product name."
            ),
        }

    product = product_result["product"]

    # Step 4: Check inventory.
    inventory_result = check_inventory(product["product_name"])

    if not inventory_result.get("success"):
        return {
            "success": False,
            "message": (
                "The inventory check failed. "
                "A quotation draft was not prepared."
            ),
        }

    inventory_records = inventory_result.get("inventory", [])

    recorded_quantities = [
        item["quantity_available"]
        for item in inventory_records
        if isinstance(item.get("quantity_available"), (int, float))
    ]

    if recorded_quantities:
        total_stock = sum(recorded_quantities)
    else:
        total_stock = None

    # Step 5: Calculate the subtotal.
    unit_price = float(product["base_price"])
    subtotal = round(unit_price * quantity, 2)

    # Step 6: Prepare the inventory message.
    if total_stock is None:
        inventory_message = (
            "Stock quantity could not be confirmed. "
            "Do not promise availability."
        )
    elif total_stock < quantity:
        inventory_message = (
            f"Warning: only {total_stock:g} units are recorded, "
            f"but {quantity} units were requested. "
            "Confirm availability before accepting the order."
        )
    else:
        inventory_message = (
            f"{total_stock:g} units are recorded in stock. "
            "Stock has not been reserved."
        )

    # Step 7: Save the draft in the database.
    conn = get_workflow_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO quotations (
                customer_id,
                product_id,
                quantity,
                unit_price,
                subtotal,
                status,
                inventory_checked
            )
            VALUES (?, ?, ?, ?, ?, 'draft', ?)
            """,
            (
                customer["customer_id"],
                product["product_id"],
                quantity,
                unit_price,
                subtotal,
                1 if total_stock is not None else 0,
            ),
        )

        quotation_id = cursor.lastrowid
        conn.commit()

    except (sqlite3.Error, KeyError, TypeError) as exc:
        conn.rollback()
        return {
            "success": False,
            "message": f"Could not save quotation draft: {exc}",
        }

    finally:
        conn.close()

    # Step 8: Return the saved draft.
    return {
        "success": True,
        "quotation_id": quotation_id,
        "status": "DRAFT - AWAITING HUMAN REVIEW",
        "customer": customer,
        "product": product,
        "quantity": quantity,
        "unit_price": unit_price,
        "subtotal": subtotal,
        "inventory_records": inventory_records,
        "recorded_stock": total_stock,
        "inventory_message": inventory_message,
        "taxes_included": False,
        "discounts_included": False,
        "delivery_charges_included": False,
        "requires_approval": True,
    }


def display_quotation_draft(result):
    """Display the quotation draft in a readable format."""

    if not result.get("success"):
        print("\nWORKFLOW ERROR")
        print(result.get("message", "The workflow failed."))
        return

    customer = result["customer"]
    product = result["product"]

    print("\n" + "=" * 45)
    print("       BUSINESS COPILOT - QUOTATION DRAFT")
    print("=" * 45)

    print(f"Quotation ID: {result['quotation_id']}")
    print(f"Status: {result['status']}")
    print(f"Customer: {customer['name']}")
    print(f"Company: {customer.get('company') or 'Not recorded'}")
    print(f"City: {customer.get('city') or 'Not recorded'}")

    print("-" * 45)
    print(f"Product: {product['product_name']}")
    print(f"Capacity: {product['capacity_tons']:g} tons")
    print(f"Quantity: {result['quantity']}")
    print(f"Base unit price: ₹{result['unit_price']:,.2f}")
    print("-" * 45)

    print(f"SUBTOTAL: ₹{result['subtotal']:,.2f}")

    print("\nPricing notes:")
    print("Taxes: Not included")
    print("Discounts: Not included")
    print("Delivery charges: Not included")

    print("\nInventory check:")

    for item in result["inventory_records"]:
        quantity = item.get("quantity_available")
        warehouse = item.get("warehouse") or "Warehouse not specified"

        if quantity is None:
            stock_text = "quantity not recorded"
        else:
            stock_text = f"{quantity:g} units recorded"

        print(f"- {warehouse}: {stock_text}")

    print(result["inventory_message"])

    print("\nIMPORTANT:")
    print("This is a saved draft, not an approved quotation.")
    print("Review the price and commercial terms before use.")
    print("No quotation has been sent to the customer.")
    print("Inventory has not been reserved.")
    print("=" * 45)


def review_quotation(quotation_id, decision, reviewer, notes=None):
    """Review a saved quotation through a web interface."""

    # Validate the quotation ID.
    if isinstance(quotation_id, bool):
        return {
            "success": False,
            "message": "A valid quotation ID is required.",
        }

    try:
        quotation_id = int(quotation_id)
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "A valid quotation ID is required.",
        }

    if quotation_id <= 0:
        return {
            "success": False,
            "message": "Quotation ID must be a positive number.",
        }

    # Validate the decision.
    if not isinstance(decision, str):
        return {
            "success": False,
            "message": "Decision must be approved or rejected.",
        }

    decision = decision.strip().lower()

    if decision not in ("approved", "rejected"):
        return {
            "success": False,
            "message": "Decision must be approved or rejected.",
        }

    # Validate reviewer and notes.
    if not isinstance(reviewer, str) or not reviewer.strip():
        return {
            "success": False,
            "message": "Reviewer name is required.",
        }

    reviewer = reviewer.strip()

    if notes is not None and not isinstance(notes, str):
        return {
            "success": False,
            "message": "Review notes must be text.",
        }

    notes = notes.strip() or None if notes is not None else None

    if notes is not None and len(notes) > 1000:
        return {
            "success": False,
            "message": "Review notes must be 1000 characters or fewer.",
        }

    conn = get_workflow_db_connection()

    try:
        # Lock the database for this review transaction.
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT status, product_id, quantity
            FROM quotations
            WHERE quotation_id = ?
            """,
            (quotation_id,),
        )

        quotation = cursor.fetchone()

        if quotation is None:
            conn.rollback()
            return {
                "success": False,
                "message": f"Quotation {quotation_id} was not found.",
            }

        current_status, product_id, requested_quantity = quotation

        if current_status != "draft":
            conn.rollback()
            return {
                "success": False,
                "message": (
                    f"Quotation {quotation_id} has already been reviewed. "
                    f"Current status: {current_status}."
                ),
            }

        # Recheck current stock before approving.
        current_stock = None

        if decision == "approved":
            cursor.execute(
                """
                SELECT SUM(quantity_available)
                FROM inventory
                WHERE product_id = ?
                  AND quantity_available IS NOT NULL
                """,
                (product_id,),
            )

            stock_row = cursor.fetchone()
            current_stock = stock_row[0] if stock_row else None

            if (
                current_stock is None
                or current_stock < requested_quantity
            ):
                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        "Approval blocked: current stock is insufficient "
                        "or cannot be confirmed. No review decision was saved."
                    ),
                    "recorded_stock": current_stock,
                    "requested_quantity": requested_quantity,
                }

        # Update the quotation only if it is still a draft.
        cursor.execute(
            """
            UPDATE quotations
            SET status = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE quotation_id = ? AND status = 'draft'
            """,
            (decision, quotation_id),
        )

        if cursor.rowcount != 1:
            conn.rollback()
            return {
                "success": False,
                "message": (
                    "The quotation status changed. "
                    "No review decision was saved."
                ),
            }

        # Record the review in the audit history.
        cursor.execute(
            """
            INSERT INTO approval_history (
                quotation_id, decision, reviewer, notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (quotation_id, decision, reviewer, notes),
        )

        conn.commit()

        if decision == "approved":
            message = (
                "Quotation approved for further processing. "
                "It has not been sent to the customer, and inventory "
                "has not been reserved."
            )
        else:
            message = (
                "Quotation rejected. The decision has been recorded. "
                "No quotation was sent and no inventory was reserved."
            )

        return {
            "success": True,
            "quotation_id": quotation_id,
            "status": decision,
            "reviewer": reviewer,
            "message": message,
            "recorded_stock": current_stock,
        }

    except sqlite3.Error as exc:
        conn.rollback()
        return {
            "success": False,
            "message": f"Could not record the review decision: {exc}",
        }

    finally:
        conn.close()


def request_human_approval(result):
    """Record human approval or rejection in the database."""

    if not result.get("success"):
        print("\nApproval unavailable: the workflow failed.")
        return

    if not result.get("requires_approval"):
        print("\nApproval unavailable: unexpected workflow state.")
        return

    quotation_id = result.get("quotation_id")

    if not quotation_id:
        print("\nApproval unavailable: quotation ID is missing.")
        return

    conn = get_workflow_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT status FROM quotations WHERE quotation_id = ?",
            (quotation_id,),
        )
        quotation = cursor.fetchone()

        if quotation is None:
            print("\nApproval unavailable: quotation was not found.")
            return

        if quotation[0] != "draft":
            print("\nThis quotation has already been reviewed.")
            print(f"Current status: {quotation[0]}")
            return

        decision = input(
            "\nApprove this quotation for further processing? (yes/no): "
        ).strip().lower()

        if decision not in ("yes", "no"):
            print("\nDecision not recognized. No changes were saved.")
            return

        # Approval is allowed only when sufficient stock is confirmed.
        if decision == "yes":
            stock = result.get("recorded_stock")
            requested = result["quantity"]

            if stock is None or stock < requested:
                print("\nAPPROVAL BLOCKED")
                print("Recorded stock is insufficient or unconfirmed.")
                print("No approval was saved.")
                return

            status = "approved"
            message = "APPROVED FOR FURTHER PROCESSING"

        else:
            status = "rejected"
            message = "REJECTED"

        reviewer = input(
            "Reviewer name (press Enter for Local Reviewer): "
        ).strip() or "Local Reviewer"

        notes = input("Review notes (optional): ").strip() or None

        cursor.execute(
            """
            UPDATE quotations
            SET status = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE quotation_id = ? AND status = 'draft'
            """,
            (status, quotation_id),
        )

        if cursor.rowcount != 1:
            conn.rollback()
            print("\nThe quotation status changed. No decision was saved.")
            return

        cursor.execute(
            """
            INSERT INTO approval_history (
                quotation_id, decision, reviewer, notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (quotation_id, status, reviewer, notes),
        )

        conn.commit()

        print(f"\nDecision: {message}")
        print(f"Quotation ID: {quotation_id}")
        print(f"Saved status: {status}")
        print(f"Reviewer: {reviewer}")
        print("The decision was saved in the database.")
        print("No quotation was sent and no inventory was reserved.")

    except sqlite3.Error as exc:
        conn.rollback()
        print(f"\nCould not save the review decision: {exc}")

    finally:
        conn.close()


if __name__ == "__main__":
    print("QUOTATION WORKFLOW")
    print("Enter the requested details below.")

    customer_name = input("Customer name: ").strip()
    product_name = input("Product name: ").strip()
    quantity = input("Quantity: ").strip()

    result = prepare_quotation_draft(
        customer_name,
        product_name,
        quantity,
    )

    display_quotation_draft(result)
    request_human_approval(result)
