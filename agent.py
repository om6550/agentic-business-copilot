
import json
import re

from llm import ask_llm
from rag_answer import answer_business_question
from tools import (
    get_db_connection,
    find_product,
    check_inventory,
    find_customer,
    find_order,
    get_business_analytics,
    get_product_analysis,
    get_all_inventory,
    get_inventory_summary,
    get_customers,
)

def normalize_text(value):
    """Normalize text for consistent English/Gujarati-mixed matching."""
    return " ".join(
        value.lower()
        .replace("_", " ")
        .split()
    )


def contains_any(text, keywords):
    """Return True if any keyword appears in the normalized text."""
    return any(keyword in text for keyword in keywords)


def make_route(tool, argument, confidence, reason):
    """Create a consistent routing decision."""
    return {
        "tool": tool,
        "argument": argument,
        "confidence": confidence,
        "reason": reason,
    }

def validate_route(route):
    """Validate the routing decision before tool execution."""

    allowed_tools = {
        "rag",
        "find_product",
        "check_inventory",
        "find_customer",
        "find_order",
        "get_product_analysis",
        "get_all_inventory",
        "get_inventory_summary",
        "get_customers",
        "get_business_analytics",
        "general",
    }

    if not isinstance(route, dict):
        return make_route(
            "general",
            "",
            0.0,
            "Routing result was invalid."
        )

    tool = route.get("tool")

    if tool not in allowed_tools:
        return make_route(
            "general",
            "",
            0.0,
            f"Unsupported tool selected: {tool}"
        )

    confidence = route.get("confidence", 0.0)

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    if confidence < 0.0 or confidence > 1.0:
        confidence = 0.0

    route["confidence"] = confidence

    return route

def validate_route_arguments(route):
    """Validate required arguments for known business tools."""

    tool = route["tool"]
    argument = route.get("argument")

    if tool in {
        "find_product",
        "check_inventory",
        "find_customer",
    }:
        if not isinstance(argument, str) or not argument.strip():
            return make_route(
                "general",
                "",
                0.0,
                f"{tool} requires a valid entity name."
            )

    if tool == "find_order":
        try:
            order_id = int(argument)
            if order_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return make_route(
                "general",
                "Please provide a valid Order ID.",
                0.0,
                "Order lookup requires a positive numeric Order ID."
            )

    if tool == "get_product_analysis":
        if not isinstance(argument, dict):
            return make_route(
                "general",
                "",
                0.0,
                "Product analysis requires valid analysis options."
            )

    if tool in {
        "get_all_inventory",
        "get_inventory_summary",
        "get_customers",
        "get_business_analytics",
        "rag",
        "general",
    }:
        return route

    return route


def choose_tool(question):
    """Select the correct business tool using database-backed routing."""

    text = normalize_text(question)

    # 1. Company policy and warranty questions -> RAG
    document_keywords = [
        "warranty", "policy", "policies", "company faq",
        "sales terms", "terms and conditions",
        "how does the company", "company policy",
    ]

    if any(word in text for word in document_keywords):
        return make_route(
            "rag",
            question,
            0.95,
            "Matched a business policy, warranty, FAQ, or terms-related question."
        )

    # Read actual names from SQLite
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT product_name FROM products WHERE active = 1")
        product_names = [row["product_name"] for row in cursor.fetchall()]

        cursor.execute("SELECT name FROM customers")
        customer_names = [row["name"] for row in cursor.fetchall()]
    finally:
        conn.close()

    # Match product and customer names, including underscores/spaces
    def normalize(value):
        return " ".join(value.lower().replace("_", " ").split())

    matched_products = [
        name for name in sorted(product_names, key=len, reverse=True)
        if normalize(name) in text
    ]

    matched_customers = [
        name for name in sorted(customer_names, key=len, reverse=True)
        if normalize(name) in text
    ]

    # Business intent vocabulary
    price_words = [
        "price", "cost", "rate", "amount",
        "bhav", "bhav ketlo", "bhav ketli",
        "kimat", "kimat ketli", "kimat ketlo",
        "કિંમત", "ભાવ",
    ]

    product_info_words = [
        "product", "details", "detail", "information",
        "info", "specification", "specs",
        "mahiti", "mahiti aapo", "vishe", "vishe janavo",
        "માહિતી", "વિશે",
    ]

    inventory_intent_words = [
        "stock", "inventory", "available", "availability",
        "stock ma", "stock maa", "available che",
        "available chhe", "stock che", "stock chhe",
        "availability che", "availability chhe",
        "સ્ટોક", "ઉપલબ્ધ", "જથ્થો",
    ]

    customer_intent_words = [
        "customer", "client", "customer details",
        "customer information",
        "customer ni mahiti",
        "grahak", "grahak ni mahiti",
        "ગ્રાહક", "કસ્ટમર",
    ]

    order_intent_words = [
        "order", "order status", "delivery status",
        "order ni mahiti", "order nu status",
        "maro order", "mara order",
        "ઓર્ડર", "ઓર્ડર સ્ટેટસ", "ડિલિવરી",
    ]

    analytics_intent_words = [
        "analytics", "summary", "overview",
        "business summary", "business analytics",
        "total customers", "total products",
        "total orders", "total inventory",
        "વ્યવસાયની માહિતી", "સારાંશ",
    ]

    # 2. Product comparison and price ranking
    comparison_words = [
        "compare", "comparison", " versus ", " vs ",
        "difference", "cheapest", "lowest price",
        "least expensive", "most expensive",
        "highest price", "costliest",
        "સૌથી સસ્તું", "સૌથી મોંઘું", "તુલના",
        "sastu", "monghu", "tulna",
    ]

    wants_cheapest = any(word in text for word in [
        "cheapest", "lowest price", "least expensive",
        "સૌથી સસ્તું", "sastu",
    ])

    wants_expensive = any(word in text for word in [
        "most expensive", "highest price", "costliest",
        "સૌથી મોંઘું", "monghu",
    ])

    wants_comparison = any(word in text for word in comparison_words)

    if wants_cheapest:
        return make_route(
            "get_product_analysis",
            {"product_names": None, "order_by": "cheapest"},
            0.95,
            "Detected a request to find the cheapest product."
        )

    if wants_expensive:
        return make_route(
            "get_product_analysis",
            {"product_names": None, "order_by": "expensive"},
            0.95,
            "Detected a request to find the most expensive product."
        )

    if wants_comparison:
        if len(matched_products) >= 2:
            return make_route(
                "get_product_analysis",
                {
                    "product_names": matched_products,
                    "order_by": None,
                },
                0.95,
                "Detected a request to compare products."
            )

        return make_route(
            "general",
            "Please mention the two product names you want to compare.",
            0.8,
            "Requested product comparison without specifying products."
        )

    # 3. Order lookup (preserve existing order functionality)
    order_keywords = [
        "order", "delivery status", "ઓર્ડર", "ડિલિવરી",
        "મારો ઓર્ડર", "ઓર્ડર સ્ટેટસ", "maro order",
        "order ni mahiti", "delivery kyare",
    ]

    if (
        any(word in text for word in order_keywords)
        or contains_any(text, order_intent_words)
    ):
        match = re.search(
            r"(?:order|ઓર્ડર)\s*#?\s*(\d+)\b",
            text,
            re.IGNORECASE
        )

        if match:
            return make_route(
                "find_order",
                match.group(1),
                0.98,
                "Detected an order request and extracted a numeric Order ID."
            )

        if any(word in text for word in [
            "total orders", "order analytics", "order summary",
        ]):
            return make_route(
                "get_business_analytics",
                "",
                0.95,
                "Detected an order analytics or order summary request."
            )

        return make_route(
            "general",
            "Please provide a valid Order ID.",
            0.85,
            "Detected an order-related question but no valid Order ID was provided."
        )

    # 4. Inventory questions
    inventory_words = [
        "stock", "inventory", "warehouse", "available",
        "how many units", "out of stock", "stock list",
        "all products", "સ્ટોક", "જથ્થો", "ઉપલબ્ધ",
        "કેટલો છે", "કેટલી છે", "કેટલા છે", "ગોડાઉન",
        "ketlo stock", "ketla stock", "stock ketlo",
        "ketla che", "ketlo che", "ketlu che",
    ]

    out_of_stock_words = [
        "out of stock", "no stock", "zero stock",
        "stock khali", "સ્ટોક ખાલી",
    ]

    total_stock_words = [
        "total inventory", "total stock", "total units",
        "warehouse total", "how many units in warehouse",
        "કુલ જથ્થો", "કુલ સ્ટોક",
    ]

    all_inventory_words = [
        "all inventory", "all stock", "inventory list",
        "stock list", "show all inventory", "show all stock",
        "out of stock products", "which products are out of stock",
        "કયા ઉત્પાદનોમાં સ્ટોક નથી",
    ]
    if any(word in text for word in out_of_stock_words):
        return make_route(
            "get_all_inventory",
            "",
            0.95,
            "Detected a request for out-of-stock inventory."
        )

    if any(word in text for word in total_stock_words):
        return make_route(
            "get_inventory_summary",
            "",
            0.95,
            "Detected a request for total inventory or stock quantity."
        )

    if any(word in text for word in all_inventory_words):
        return make_route(
            "get_all_inventory",
            "",
            0.95,
            "Detected a request to view the inventory list."
        )

    if (
    any(word in text for word in inventory_words)
    or contains_any(text, inventory_intent_words)
):
        if matched_products:
            return make_route(
                "check_inventory",
                matched_products[0],
                0.95,
                "Detected a request to check inventory for a specific product."
            )
        return make_route(
            "get_all_inventory",
            "",
            0.95,
            "Detected a general request to view inventory."
        )

   # 5. Individual customer lookup
    if matched_customers:
        return make_route(
            "find_customer",
            matched_customers[0],
            0.98,
            "Matched a registered customer name in the question."
        )


    # 6. Individual product details / price
    if matched_products:

        if contains_any(text, price_words):
            return make_route(
                "find_product",
                matched_products[0],
                0.98,
                "Matched a product name and detected a price-related intent."
            )

        if contains_any(text, product_info_words):
            return make_route(
                "find_product",
                matched_products[0],
                0.97,
                "Matched a product name and detected a product-information intent."
            )

        return make_route(
            "find_product",
            matched_products[0],
            0.95,
            "Matched a registered active product name."
        )


    # 7. General customer questions / customer list
    customer_words = [
        "customer", "customers", "client", "clients",
        "ગ્રાહક", "કસ્ટમર", "customer ni mahiti",
        "customer kon che", "grahak ni mahiti",
    ]

    active_words = [
        "active", "active customers", "સક્રિય", "chalu customers"
    ]

    all_customer_words = [
        "all customers", "list customers", "show customers",
        "customer list", "active customers",
        "બધા ગ્રાહકો", "બધા કસ્ટમર",
    ]

    if (
        any(word in text for word in customer_words)
        or contains_any(text, customer_intent_words)
    ):
        status = (
            "active"
            if any(word in text for word in active_words)
            else None
        )

        return make_route(
            "get_customers",
            {"status": status},
            0.95,
            "Detected a request for the customer list."
        )
def route_question(question):
    """Choose and validate a business route."""

    route = choose_tool(question)
    route = validate_route(route)
    route = validate_route_arguments(route)

    if route["tool"] != "general" and route["confidence"] < 0.60:
        return make_route(
            "general",
            "",
            route["confidence"],
            "Routing confidence is too low to safely execute a business tool."
        )

    return route

def execute_tool(tool_name, argument, language="English"):
    """Execute only explicitly allowed business functions."""

    if tool_name == "rag":
        return {
            "success": True,
            "answer": answer_business_question(
                argument,
                language=language,
            )
        }

    if tool_name == "find_product":
        return find_product(argument)

    if tool_name == "check_inventory":
        return check_inventory(argument)

    if tool_name == "find_customer":
        return find_customer(argument)

    if tool_name == "find_order":
        try:
            order_id = int(argument)
        except ValueError:
            return {
                "success": False,
                "message": "A valid numeric order ID is required."
            }

        if order_id <= 0:
            return {
                "success": False,
                "message": "Order ID must be a positive number."
            }

        return find_order(order_id)
    
    if tool_name == "get_product_analysis":
        options = argument if isinstance(argument, dict) else {}
        return get_product_analysis(
            product_names=options.get("product_names"),
            order_by=options.get("order_by"),
        )

    if tool_name == "get_all_inventory":
        result = get_all_inventory()
        if result.get("success") and isinstance(argument, dict):
            if argument.get("out_of_stock_only"):
                result["inventory"] = [
                    item for item in result["inventory"]
                    if item["stock_records"] > 0
                    and item["total_quantity"] is not None
                    and item["total_quantity"] <= 0
                ]
        return result

    if tool_name == "get_inventory_summary":
        return get_inventory_summary()

    if tool_name == "get_customers":
        options = argument if isinstance(argument, dict) else {}
        return get_customers(status=options.get("status"))

    if tool_name == "get_business_analytics":
        return get_business_analytics()


    return {
        "success": False,
        "message": "No matching business tool was selected."
    }


def format_result(tool_name, result, language="English"):
    """Format verified business results in English or Gujarati-English."""

    if not result.get("success"):
        return result.get(
            "message",
            "The request could not be completed."
        )

    gujarati_mixed = language == "Gujarati + English"

    if tool_name == "rag":
        return result["answer"]

    if tool_name == "find_product":
        product = result["product"]

        name = product["product_name"]
        price = f"₹{product['base_price']:,.0f}"
        capacity = f"{product['capacity_tons']:g}"

        if gujarati_mixed:
            return (
                f"**{name}** ની base price {price} છે "
                f"અને તેની capacity {capacity} tons છે.\n\n"
                f"Description: {product['description']}"
            )

        return (
            f"{name} has a base price of {price} "
            f"and a capacity of {capacity} tons. "
            f"Description: {product['description']}"
        )

    if tool_name == "check_inventory":
        records = result["inventory"]
        lines = []

        for item in records:
            quantity = item["quantity_available"]
            warehouse = item["warehouse"] or "Warehouse not specified"

            if quantity is None:
                stock_text = (
                    "Stock quantity નોંધાયેલ નથી."
                    if gujarati_mixed
                    else "Stock quantity is not recorded"
                )
            else:
                stock_text = (
                    f"{quantity} units stock માં નોંધાયેલા છે."
                    if gujarati_mixed
                    else f"{quantity} units recorded in stock"
                )

            if gujarati_mixed:
                lines.append(
                    f"**{item['product_name']}**: {stock_text} "
                    f"Warehouse: {warehouse}."
                )
            else:
                lines.append(
                    f"{item['product_name']}: {stock_text} "
                    f"at {warehouse}."
                )

        return "\n".join(lines)

    if tool_name == "find_customer":
        customer = result["customer"]

        if gujarati_mixed:
            return (
                f"**Customer:** {customer['name']}\n\n"
                f"**Company:** {customer['company'] or 'Not recorded'}\n\n"
                f"**City:** {customer['city'] or 'Not recorded'}\n\n"
                f"**Customer type:** "
                f"{customer['customer_type'] or 'Not recorded'}\n\n"
                f"**Interested product:** "
                f"{customer['interested_product'] or 'Not recorded'}\n\n"
                f"**Status:** {customer['status']}"
            )

        return (
            f"Customer: {customer['name']}. "
            f"Company: {customer['company'] or 'Not recorded'}. "
            f"City: {customer['city'] or 'Not recorded'}. "
            f"Customer type: "
            f"{customer['customer_type'] or 'Not recorded'}. "
            f"Interested product: "
            f"{customer['interested_product'] or 'Not recorded'}. "
            f"Status: {customer['status']}."
        )

    if tool_name == "find_order":
        order = result["order"]

        if gujarati_mixed:
            return (
                f"**Order {order['order_id']}**\n\n"
                f"**Customer:** {order['customer_name']}\n\n"
                f"**Product:** {order['product_name']}\n\n"
                f"**Quantity:** {order['quantity']}\n\n"
                f"**Order amount:** ₹{order['total_amount']:,.0f}\n\n"
                f"**Order status:** {order['order_status']}\n\n"
                f"**Delivery status:** {order['delivery_status']}"
            )

        return (
            f"Order {order['order_id']} belongs to "
            f"{order['customer_name']}. "
            f"Product: {order['product_name']}. "
            f"Quantity: {order['quantity']}. "
            f"Recorded order amount: "
            f"₹{order['total_amount']:,.0f}. "
            f"Order status: {order['order_status']}. "
            f"Delivery status: {order['delivery_status']}."
        )

    

    if tool_name == "get_product_analysis":
        lines = (
            ["**Product Analysis (ઉત્પાદનોની તુલના)**"]
            if gujarati_mixed else ["**Product Analysis**"]
        )

        for item in result["products"]:
            if gujarati_mixed:
                lines.append(
                    f"- **{item['product_name']}** | "
                    f"કિંમત: ₹{item['base_price']:,.0f} | "
                    f"ક્ષમતા: {item['capacity_tons']:g} tons"
                )
            else:
                lines.append(
                    f"- **{item['product_name']}** | "
                    f"Price: ₹{item['base_price']:,.0f} | "
                    f"Capacity: {item['capacity_tons']:g} tons"
                )

        return "\n".join(lines)

    if tool_name == "get_all_inventory":
        records = result["inventory"]

        if not records:
            return (
                "કોઈ out-of-stock product મળ્યું નથી."
                if gujarati_mixed
                else "No matching products found."
            )

        lines = [
            "**Inventory Report (સ્ટોકની માહિતી)**"
            if gujarati_mixed else "**Inventory Report**"
        ]

        for item in records:
            quantity = item["total_quantity"]
            warehouses = item["warehouses"] or "Not specified"

            if quantity is None:
                stock = "નોંધાયેલ નથી" if gujarati_mixed else "Not recorded"
            else:
                stock = (
                    f"{quantity} units ઉપલબ્ધ છે"
                    if gujarati_mixed else f"{quantity} units"
                )

            lines.append(
                f"- **{item['product_name']}**: {stock} | "
                f"Warehouse: {warehouses}"
            )

        return "\n".join(lines)

    if tool_name == "get_inventory_summary":
        summary = result["summary"]

        if gujarati_mixed:
            return (
                f"**કુલ Warehouse Stock:** "
                f"{summary['total_inventory_units']} units\n\n"
                f"**Stock વગરના Products:** "
                f"{summary['out_of_stock_products'] or 0}\n\n"
                f"**Stock Record ઉપલબ્ધ નથી:** "
                f"{summary['products_without_stock_records'] or 0}"
            )

        return (
            f"**Total warehouse stock:** "
            f"{summary['total_inventory_units']} units\n\n"
            f"**Out-of-stock products:** "
            f"{summary['out_of_stock_products'] or 0}\n\n"
            f"**Products without stock records:** "
            f"{summary['products_without_stock_records'] or 0}"
        )

    if tool_name == "get_customers":
        customers = result["customers"]

        if not customers:
            return "કોઈ Customer મળ્યો નથી." if gujarati_mixed else "No customers found."

        heading = (
            f"**Customer List ({result['count']})**"
            if not gujarati_mixed
            else f"**Customer List (ગ્રાહકો: {result['count']})**"
        )
        lines = [heading]

        for customer in customers:
            city = customer["city"] or "Not recorded"
            interested = customer["interested_product"] or "Not recorded"

            if gujarati_mixed:
                lines.append(
                    f"- **{customer['name']}** | "
                    f"શહેર: {city} | "
                    f"Interested Product: {interested} | "
                    f"Status: {customer['status']}"
                )
            else:
                lines.append(
                    f"- **{customer['name']}** | "
                    f"City: {city} | "
                    f"Interested Product: {interested} | "
                    f"Status: {customer['status']}"
                )

        return "\n".join(lines)

    if tool_name == "get_business_analytics":
        overview = result["overview"]
        inventory = result["inventory"]
        orders = result["orders"]

        if gujarati_mixed:
            return (
                "**Business Overview (વ્યવસાયની માહિતી)**\n\n"
                f"કુલ Customers: {overview['total_customers']}\n\n"
                f"Active Products: {overview['active_products']}\n\n"
                f"કુલ Inventory: {inventory['total_inventory_units']} units\n\n"
                f"Out-of-stock Products: {inventory['out_of_stock_products'] or 0}\n\n"
                f"કુલ Orders: {orders['total_orders']}\n\n"
                f"Recorded Order Value: "
                f"₹{orders['total_recorded_order_value']:,.0f}"
            )

        return (
            f"**Business Overview**\n\n"
            f"Customers: {overview['total_customers']}\n\n"
            f"Active products: {overview['active_products']}\n\n"
            f"Inventory units: {inventory['total_inventory_units']}\n\n"
            f"Out-of-stock products: {inventory['out_of_stock_products'] or 0}\n\n"
            f"Total orders: {orders['total_orders']}\n\n"
            f"Recorded order value: "
            f"₹{orders['total_recorded_order_value']:,.0f}"
        )


    return (
    "I couldn't identify a supported business request. "
    "Please ask about products, prices, inventory, customers, "
    "orders, business analytics, or company policies."
)


if __name__ == "__main__":
    question = input("Ask your business copilot: ").strip()

    if not question:
        print("Please enter a question.")
    else:
        selection = route_question(question)

        print("\nSelected tool:")
        print(selection)

        result = execute_tool(
            selection["tool"],
            selection["argument"]
        )

        print("\nBUSINESS COPILOT ANSWER:")
        print(format_result(selection["tool"], result))
