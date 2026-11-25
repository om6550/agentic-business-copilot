import streamlit as st

import requests

from pathlib import Path

from textwrap import dedent

from tools import get_business_analytics

from agent import choose_tool, execute_tool, format_result

from tools import get_quotation_analytics


# --------------------------------------------------

# Page configuration

# --------------------------------------------------

st.set_page_config(

    page_title="Business Operations Copilot",

    page_icon="🤖",

    layout="wide",

)





# --------------------------------------------------

# LAXMI ENGINEERING TRAILER BRANDING

# --------------------------------------------------



ASSET_DIR = Path(__file__).resolve().parent / "assets"



LOGO_PATH = ASSET_DIR / "laxmi_logo.jpeg"

HERO_IMAGE_PATH = ASSET_DIR / "trailer_red_side_01.jpeg"

st.markdown(
    dedent("""
<style>

    .laxmi-brand-panel {

        background: linear-gradient(135deg, #241512, #651b1b);

        border: 1px solid rgba(255, 200, 80, 0.35);

        border-radius: 16px;

        padding: 32px 26px;

        min-height: 300px;

        display: flex;

        flex-direction: column;

        justify-content: center;

        box-sizing: border-box;

    }



    .laxmi-eyebrow {

        color: #ffd166;

        font-size: 12px;

        font-weight: 800;

        letter-spacing: 2px;

        margin-bottom: 14px;

    }



    .laxmi-title {

        color: #ffffff;

        font-size: clamp(25px, 2.2vw, 38px);

        font-weight: 800;

        line-height: 1.2;

        margin-bottom: 14px;

    }



    .laxmi-subtitle {

        color: #f5e9e5;

        font-size: 15px;

        line-height: 1.6;

    }



    .laxmi-tagline {

        color: #ffd166;

        font-size: 12px;

        font-weight: 700;

        margin-top: 22px;

        line-height: 1.8;

    }



    div[data-testid="stImage"] img {

        border-radius: 16px;

    }

    </style>
    """),
    unsafe_allow_html=True,
)



hero_text, hero_photo = st.columns(

    [0.95, 1.25],

    gap="large",

    vertical_alignment="center",

)




with hero_text:
    st.markdown(
        """
<div class="laxmi-brand-panel">
    <div class="laxmi-eyebrow">LAXMI ENGINEERING TRAILER</div>
    <div class="laxmi-title">Business Operations Copilot</div>
    <div class="laxmi-subtitle">
        Your intelligent assistant for trailer business operations.
    </div>
    <div class="laxmi-tagline">
        PRODUCTS &bull; QUOTATIONS<br>
        INVENTORY &bull; ORDERS
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )




with hero_photo:

    if HERO_IMAGE_PATH.exists():

        st.image(

            str(HERO_IMAGE_PATH),

            caption="Laxmi Engineering Trailer · Hydraulic Trailer",

            use_container_width=True,

        )

    else:

        st.warning(

            "Trailer image not found. Check the assets folder."

        )



st.caption(

    "Local AI assistant powered by your existing Python agent "

    "and business database."

)





# --------------------------------------------------

# Sidebar

# --------------------------------------------------


with st.sidebar:
    if LOGO_PATH.exists():
        st.image(
            str(LOGO_PATH),
            use_container_width=True,
        )
    else:
        st.warning("Laxmi logo not found in assets folder.")

    st.header("Control Panel")

    st.subheader("Navigation")

    selected_page = st.radio(
        "Select Workspace",
        ["Business Chat", "Business Dashboard", "Customer Management"],
        index=0,
    )

    st.divider()

    st.subheader("Language Settings")

    response_language = st.selectbox(
        "Response Language",
        [
            "English",
            "Gujarati + English",
        ],
        index=0,
    )

    st.subheader("System Status")

    try:
        response = requests.get(
            "http://127.0.0.1:8000/health",
            timeout=2,
        )

        if response.ok and response.json().get("success"):
            st.success("Business API: Connected")
        else:
            st.warning("Business API: Unexpected response")

    except requests.RequestException:
        st.warning("Business API: Offline")

    st.info("Chat uses your existing Python business agent.")

    st.divider()

    st.subheader("Example Questions")

    st.markdown(
        """
        - What is the price of the Hydraulic Trailer?
        - What is the capacity of the Heavy Duty Trailer?
        - Check inventory for Hydraulic Trailer.
        - Find customer Rajesh Patel.
        - What is the delivery status of order 1?
        - What is the company warranty policy?
        """
    )

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# --------------------------------------------------
# Business Intelligence Dashboard
# --------------------------------------------------

if selected_page == "Business Dashboard":

    st.title("📊 Business Intelligence Dashboard")

    st.caption(
        "Laxmi Engineering Trailer | Business Performance Overview"
    )

    analytics = get_business_analytics()

    if not analytics.get("success"):
        st.error(analytics.get("message", "Analytics unavailable."))

    else:
        overview = analytics["overview"]
        inventory = analytics["inventory"]
        orders = analytics["orders"]

        st.subheader("Business Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Customers",
            overview["total_customers"]
        )

        col2.metric(
            "Active Products",
            overview["active_products"]
        )

        col3.metric(
            "Total Orders",
            orders["total_orders"]
        )

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Inventory Units",
            inventory["total_inventory_units"]
        )

        col5.metric(
            "Out of Stock Products",
            inventory["out_of_stock_products"]
        )

        col6.metric(
            "Recorded Order Value",
            f"₹{orders['total_recorded_order_value']:,.0f}"
        )

        st.divider()

        # --------------------------------------------------
        # MARKETING PRESENCE
        # --------------------------------------------------

        st.subheader("📱 Marketing Presence")

        marketing_col1, marketing_col2 = st.columns([1.5, 1])

        with marketing_col1:
            st.markdown("### 📸 @laxmi_trailer_undel")

            st.caption(
                "Premium Laxmi Trailer Manufacturer"
            )

            st.write(
                "Product showcases • Manufacturing • Trailer deliveries"
            )

            st.markdown(
                "Follow our latest trailer products, manufacturing work, "
                "and customer deliveries on Instagram."
            )

        with marketing_col2:
            st.markdown("### Instagram")

            st.link_button(
                "📸 View Instagram Profile ↗",
                "https://www.instagram.com/laxmi_trailer_undel/",
                use_container_width=True,
            )

            st.caption(
                "Official Laxmi Trailer Undel Instagram"
            )

        st.divider()

# Order Analytics
        
        # Quotation Analytics
        st.divider()
        st.header("🧾 Quotation Analytics")

        quotation_data = get_quotation_analytics()

        if quotation_data.get("success"):
            summary = quotation_data["summary"]

            st.subheader("Quotation Overview")

            q1, q2, q3, q4 = st.columns(4)

            q1.metric("Total Quotations", summary["total_quotations"])
            q2.metric("Approved", summary["approved"])
            q3.metric("Draft", summary["draft"])
            q4.metric("Rejected", summary["rejected"])

            st.metric(
                "Approved Quotation Value",
                f"₹{summary['approved_quotation_value']:,.0f}"
            )

            st.subheader("Product-wise Quotations")

            quotation_products = quotation_data["products"]

            if quotation_products:
                st.bar_chart(
                    {
                        "Product": [
                            item["product_name"]
                            for item in quotation_products
                        ],
                        "Quotation Count": [
                            item["quotation_count"]
                            for item in quotation_products
                        ],
                    },
                    x="Product",
                    y="Quotation Count",
                )

                st.dataframe(
                    quotation_products,
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.error(
                quotation_data.get(
                    "message",
                    "Quotation analytics unavailable."
                )
            )


        st.success("Business analytics loaded successfully.")


# --------------------------------------------------
# CUSTOMER MANAGEMENT
# --------------------------------------------------

if selected_page == "Customer Management":

    st.title("Customer Management")
    st.caption(
        "Laxmi Engineering Trailer | Customer Registration "
        "and Directory"
    )

    st.divider()

    # ----------------------------------------------
    # CUSTOMER REGISTRATION
    # ----------------------------------------------

    st.subheader("Add New Customer")

    st.caption(
        "Register a customer before generating their quotation."
    )

    with st.form(
        "customer_registration_form",
        clear_on_submit=True
    ):

        col1, col2 = st.columns(2)

        with col1:

            customer_name = st.text_input(
                "Customer Name *",
                placeholder="e.g. Amit Shah"
            )

            phone = st.text_input(
                "Phone Number *",
                placeholder="e.g. 9876543210"
            )

            company = st.text_input(
                "Company Name",
                placeholder="Optional"
            )

            city = st.text_input(
                "City",
                placeholder="e.g. Ahmedabad"
            )

        with col2:

            customer_type = st.selectbox(
                "Customer Type",
                [
                    "Farmer",
                    "Tractor Owner",
                    "Dealer",
                    "Agricultural Business",
                    "Transport Business",
                    "Other",
                ]
            )

            interested_product = st.selectbox(
                "Interested Product",
                [
                    "Not specified",
                    "Standard Tractor Trailer",
                    "Hydraulic Trailer",
                    "Heavy Duty Trailer",
                    "Agriculture Trailer Pro",
                    "Custom Trailer",
                ]
            )

        submitted = st.form_submit_button(
            "Register Customer",
            type="primary",
            use_container_width=True
        )

    if submitted:

        if not customer_name.strip():

            st.error("Please enter the customer name.")

        elif not phone.strip():

            st.error("Please enter the customer's phone number.")

        else:

            payload = {
                "name": customer_name.strip(),
                "phone": phone.strip(),
                "company": company.strip(),
                "city": city.strip(),
                "customer_type": customer_type,
                "interested_product": (
                    ""
                    if interested_product == "Not specified"
                    else interested_product
                ),
            }

            try:

                response = requests.post(
                    "http://127.0.0.1:8000/customers",
                    json=payload,
                    timeout=10,
                )

                try:
                    data = response.json()
                except ValueError:
                    data = {}

                if response.ok and data.get("success"):

                    customer = data.get("customer", {})

                    st.success(
                        f"Customer registered successfully! "
                        f"Customer ID: {customer.get('customer_id')}"
                    )

                else:

                    st.error(
                        data.get(
                            "message",
                            f"Registration failed. HTTP {response.status_code}."
                        )
                    )

            except requests.RequestException as error:

                st.error(
                    f"Could not connect to Business API: {error}"
                )

    st.divider()

    # ----------------------------------------------
    # CUSTOMER DIRECTORY
    # ----------------------------------------------

    st.subheader("Customer Directory")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:

        search_term = st.text_input(
            "Search Customers",
            placeholder="Search name, phone or company..."
        )

    with filter_col2:

        status_filter = st.selectbox(
            "Customer Status",
            ["All", "active", "inactive"]
        )

    params = {}

    if search_term.strip():
        params["search"] = search_term.strip()

    if status_filter != "All":
        params["status"] = status_filter

    try:

        response = requests.get(
            "http://127.0.0.1:8000/customers",
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("success"):

            customers = data.get("customers", [])

            st.metric(
                "Matching Customers",
                data.get("count", len(customers))
            )

            if customers:

                st.dataframe(
                    customers,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info("No customers found matching your filters.")

        else:

            st.error(
                data.get(
                    "message",
                    "Could not load customer records."
                )
            )

    except requests.RequestException as error:

        st.error(f"Could not load customers: {error}")

    except ValueError:

        st.error("The API returned an invalid response.")


    # --------------------------------------------------
    # CUSTOMER PROFILE & QUOTATION HISTORY
    # --------------------------------------------------

    st.divider()

    st.subheader("Customer Profile & Quotation History")

    st.caption(
        "Select a registered customer to view their profile "
        "and complete quotation history."
    )

    try:
        # Load customers for the profile selector.
        profile_response = requests.get(
            "http://127.0.0.1:8000/customers",
            timeout=10
        )

        profile_response.raise_for_status()
        profile_data = profile_response.json()

        if not profile_data.get("success"):
            st.error(
                profile_data.get(
                    "message",
                    "Could not load customers."
                )
            )

        else:
            profile_customers = profile_data.get("customers", [])

            if not profile_customers:
                st.info("No customers available.")

            else:
                # Create a lookup using customer IDs.
                profile_customer_by_id = {
                    int(customer["customer_id"]): customer
                    for customer in profile_customers
                }

                # Customer selector.
                selected_profile_id = st.selectbox(
                    "Select Customer",
                    options=list(profile_customer_by_id.keys()),
                    format_func=lambda customer_id: (
                        f"{profile_customer_by_id[customer_id]['name']} "
                        f"(ID: {customer_id})"
                    ),
                    key="customer_profile_selector"
                )

                # --------------------------------------
                # LOAD CUSTOMER PROFILE
                # --------------------------------------

                profile_response = requests.get(
                    f"http://127.0.0.1:8000/customers/{selected_profile_id}",
                    timeout=10
                )

                profile_response.raise_for_status()
                profile_result = profile_response.json()

                if not profile_result.get("success"):
                    st.error(
                        profile_result.get(
                            "message",
                            "Could not load customer profile."
                        )
                    )

                else:
                    customer_profile = profile_result["customer"]

                    st.markdown("### Customer Details")

                    st.write(
                        "**Customer Name:**",
                        customer_profile.get("name") or "Not recorded"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.write("**Customer ID**")
                    col1.write(customer_profile.get("customer_id"))

                    col2.write("**Phone**")
                    col2.write(
                        customer_profile.get("phone") or "Not recorded"
                    )

                    col3.write("**Company**")
                    col3.write(
                        customer_profile.get("company") or "Not recorded"
                    )

                    col4, col5, col6 = st.columns(3)

                    col4.write("**City**")
                    col4.write(
                        customer_profile.get("city") or "Not recorded"
                    )

                    col5.write("**Customer Type**")
                    col5.write(
                        customer_profile.get("customer_type") or "Not recorded"
                    )

                    col6.write("**Interested Product**")
                    col6.write(
                        customer_profile.get("interested_product")
                        or "Not recorded"
                    )

                    st.write(
                        "**Account Status:**",
                        customer_profile.get("status", "Not recorded").title()
                    )

                    # ----------------------------------
                    # LOAD QUOTATION HISTORY
                    # ----------------------------------

                    st.divider()
                    st.markdown("### Quotation History")

                    history_response = requests.get(
                        f"http://127.0.0.1:8000/customers/{selected_profile_id}/quotations",
                        timeout=10
                    )

                    history_response.raise_for_status()
                    history_data = history_response.json()

                    if not history_data.get("success"):
                        st.error(
                            history_data.get(
                                "message",
                                "Could not load quotation history."
                            )
                        )

                    else:
                        quotations = history_data.get("quotations", [])

                        if quotations:
                            total_quotations = len(quotations)

                            draft_count = sum(
                                1 for q in quotations
                                if str(q.get("status", "")).lower() == "draft"
                            )

                            approved_count = sum(
                                1 for q in quotations
                                if str(q.get("status", "")).lower() == "approved"
                            )

                            rejected_count = sum(
                                1 for q in quotations
                                if str(q.get("status", "")).lower() == "rejected"
                            )

                            total_quoted_value = sum(
                                float(q.get("subtotal") or 0)
                                for q in quotations
                            )

                            metric1, metric2, metric3, metric4 = st.columns(4)

                            metric1.metric(
                                "Total Quotations",
                                total_quotations
                            )

                            metric2.metric("Draft", draft_count)
                            metric3.metric("Approved", approved_count)
                            metric4.metric("Rejected", rejected_count)

                            st.metric(
                                "Total Quoted Value (all statuses)",
                                f"₹{total_quoted_value:,.2f}"
                            )

                            # Prepare readable quotation table.
                            quotation_rows = []

                            for quotation in quotations:
                                quotation_rows.append({
                                    "Quotation ID": (
                                        f"#{quotation['quotation_id']}"
                                    ),
                                    "Product": quotation.get(
                                        "product_name", "Not recorded"
                                    ),
                                    "Quantity": quotation.get("quantity", 0),
                                    "Unit Price": (
                                        f"₹{float(quotation.get('unit_price') or 0):,.2f}"
                                    ),
                                    "Subtotal": (
                                        f"₹{float(quotation.get('subtotal') or 0):,.2f}"
                                    ),
                                    "Status": str(
                                        quotation.get("status", "unknown")
                                    ).title(),
                                    "Created At": quotation.get(
                                        "created_at", "Not recorded"
                                    ),
                                    "Reviewed At": quotation.get(
                                        "reviewed_at"
                                    ) or "Not reviewed"
                                })

                            st.dataframe(
                                quotation_rows,
                                use_container_width=True,
                                hide_index=True
                            )

                        else:
                            st.info(
                                "No quotations have been created "
                                "for this customer yet."
                            )

    except requests.RequestException as error:
        st.error(
            f"Could not connect to the Business API: {error}"
        )

    except (ValueError, KeyError, TypeError) as error:
        st.error(
            f"Could not display customer information: {error}"
        )


    st.stop()


# --------------------------------------------------

# Chat history

# --------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = []





for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])



        if message.get("tool"):

            with st.expander("View tool routing details"):

                st.write("Selected tool:", message["tool"])

                st.write("Tool argument:", message["argument"])





# --------------------------------------------------

# Process a new question

# --------------------------------------------------

question = st.chat_input(

    "Ask your business copilot a question..."

)



if question:

    st.session_state.messages.append(

        {

            "role": "user",

            "content": question,

        }

    )



    with st.chat_message("user"):

        st.markdown(question)



    with st.chat_message("assistant"):

        with st.spinner("Analyzing your question..."):
            try:
                # Step 1: Select the appropriate tool
                selection = choose_tool(question)

                # Step 2: Execute the selected tool
                result = execute_tool(
                    selection["tool"],
                    selection["argument"],
                    language=response_language,
                )

                # Step 3: Format the result
                answer = format_result(
                    selection["tool"],
                    result,
                    language=response_language,
                )

                st.markdown(answer)

            except Exception as error:
                st.error(f"Something went wrong: {error}")



                with st.expander("View tool routing details"):

                    st.write("Selected tool:", selection["tool"])

                    st.write(

                        "Tool argument:",

                        selection["argument"],

                    )



                st.session_state.messages.append(

                    {

                        "role": "assistant",

                        "content": answer,

                        "tool": selection["tool"],

                        "argument": selection["argument"],

                    }

                )



            except Exception as error:

                st.error(

                    "The assistant encountered an error while "

                    "processing your question."

                )

                st.caption(

                    f"Technical details: {type(error).__name__}: {error}"

                )







# --------------------------------------------------

# QUOTATION GENERATOR

# --------------------------------------------------



st.divider()

st.header("🧾 Quotation Generator")

st.caption(

    "Prepare a quotation draft for review. "

    "Creating a draft does not approve or send it."

)



if "quotation_result" not in st.session_state:

    st.session_state.quotation_result = None



if "quotation_error" not in st.session_state:

    st.session_state.quotation_error = None






# --------------------------------------------------
# LOAD REGISTERED CUSTOMERS
# --------------------------------------------------

active_customers = []
customer_by_id = {}
customer_load_error = None

try:
    customer_response = requests.get(
        "http://127.0.0.1:8000/customers",
        timeout=5,
    )

    customer_response.raise_for_status()
    customer_data = customer_response.json()

    if not customer_data.get("success"):
        raise ValueError(
            customer_data.get(
                "message",
                "Could not load customers."
            )
        )

    all_customers = customer_data.get("customers", [])

    active_customers = [
        customer
        for customer in all_customers
        if str(customer.get("status", "")).lower() == "active"
    ]

    customer_by_id = {
        int(customer["customer_id"]): customer
        for customer in active_customers
    }

except (requests.RequestException, ValueError, KeyError) as error:
    customer_load_error = str(error)


# --------------------------------------------------
# QUOTATION FORM
# --------------------------------------------------

submitted = False
selected_customer_id = None

if customer_load_error:

    st.error(
        f"Could not load registered customers: {customer_load_error}"
    )

elif not active_customers:

    st.warning(
        "No active customers found. "
        "Please register a customer in Customer Management first."
    )

else:

    with st.form("quotation_form"):

        selected_customer_id = st.selectbox(
            "Select Registered Customer",
            options=list(customer_by_id.keys()),
            format_func=lambda customer_id: (
                f"{customer_by_id[customer_id]['name']} | "
                f"{customer_by_id[customer_id].get('company') or 'Individual'} | "
                f"{customer_by_id[customer_id].get('city') or 'City not recorded'}"
            ),
        )

        selected_customer = customer_by_id[selected_customer_id]

        st.caption(
            f"Customer ID: {selected_customer_id} | "
            f"Phone: {selected_customer.get('phone') or 'Not recorded'}"
        )

        product_name = st.selectbox(
            "Select product",
            [
                "Standard Tractor Trailer",
                "Hydraulic Trailer",
                "Heavy Duty Trailer",
                "Agriculture Trailer Pro",
                "Custom Trailer",
            ],
        )

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            max_value=1000,
            value=1,
            step=1,
        )

        submitted = st.form_submit_button(
            "Generate Quotation Draft",
            use_container_width=True,
        )


# --------------------------------------------------
# SUBMIT QUOTATION THROUGH EXISTING N8N WORKFLOW
# --------------------------------------------------

if submitted:

    st.session_state.quotation_result = None
    st.session_state.quotation_error = None

    customer = customer_by_id.get(selected_customer_id)

    if not customer:

        st.session_state.quotation_error = (
            "Please select a valid registered customer."
        )

    else:

        try:

            response = requests.post(
                "http://127.0.0.1:8000/quotation/automate",
                json={
                    "customer_name": customer["name"],
                    "product_name": product_name,
                    "quantity": int(quantity),
                },
                timeout=60,
            )

            try:
                data = response.json()
            except ValueError:
                data = {}

            if response.ok and data.get("success"):

                st.session_state.quotation_result = data

            else:

                st.session_state.quotation_error = data.get(
                    "message",
                    f"Automation failed. HTTP {response.status_code}.",
                )

        except requests.Timeout:

            st.session_state.quotation_error = (
                "The automation request timed out. "
                "Check the n8n execution before retrying "
                "to avoid creating a duplicate quotation."
            )

        except requests.RequestException as error:

            st.session_state.quotation_error = (
                f"Could not connect to the Business Copilot API: {error}"
            )




# --------------------------------------------------

# DISPLAY QUOTATION RESULT

# --------------------------------------------------



if st.session_state.quotation_error:

    st.error(st.session_state.quotation_error)


quotation = st.session_state.quotation_result
if quotation:
    st.write("DEBUG: Actual API response received:")
    st.json(quotation)


if quotation:

    customer = quotation.get("customer") or {}

    product = quotation.get("product") or {}



    quotation_status = str(

        quotation.get("status", "")

    ).strip().lower()



    # Display the current quotation status.

    if quotation_status == "approved":

        st.success(

            f"Quotation {quotation.get('quotation_id')} "

            "approved for further processing."

        )

    elif quotation_status == "rejected":

        st.warning(

            f"Quotation {quotation.get('quotation_id')} has been rejected."

        )

    else:

        st.success(

            f"Quotation draft saved. "

            f"Quotation ID: {quotation.get('quotation_id')}"

        )



    # Quotation summary.

    st.subheader("Quotation Summary")



    col1, col2, col3 = st.columns(3)



    with col1:

        st.metric(

            "Base Unit Price",

            f"₹{float(quotation['unit_price']):,.2f}",

        )



    with col2:

        st.metric("Quantity", quotation["quantity"])



    with col3:

        st.metric(

            "Subtotal",

            f"₹{float(quotation['subtotal']):,.2f}",

        )



    st.markdown("#### Customer Details")

    st.write("Customer:", customer.get("name", "Not recorded"))

    st.write("Company:", customer.get("company") or "Not recorded")

    st.write("City:", customer.get("city") or "Not recorded")



    st.markdown("#### Product Details")

    st.write(

        "Product:",

        product.get("product_name", "Not recorded"),

    )

    st.write(

        "Capacity:",

        f"{product.get('capacity_tons', 'Not recorded')} tons",

    )

    st.write("Status:", quotation.get("status", "Draft"))



    st.markdown("#### Inventory Check")

    st.info(

        quotation.get(

            "inventory_message",

            "Inventory information is unavailable.",

        )

    )



    for item in quotation.get("inventory_records", []):

        stock = item.get("quantity_available")



        if stock is None:

            stock_text = "Stock quantity not recorded"

        else:

            stock_text = f"{stock:g} units recorded"



        st.write(

            f"- {item.get('warehouse') or 'Warehouse not specified'}: "

            f"{stock_text}"

        )



   
    # Human review controls.
    st.markdown("#### Quotation Review")

    if quotation_status in ("approved", "rejected"):
        st.info(
            quotation.get(
                "review_message",
                "The review decision has been recorded.",
            )
        )
        st.write(
            "Reviewer:",
            quotation.get("reviewer", "Not recorded"),
        )

    else:
        st.warning(
            "This is a draft awaiting human review. Taxes, discounts, "
            "and delivery charges are not included. The quotation has "
            "not been sent, and inventory has not been reserved."
        )

        with st.form("quotation_review_form"):
            reviewer_name = st.text_input(
                "Reviewer name",
                value="Local Reviewer",
            )

            review_notes = st.text_area(
                "Review notes (optional)",
                max_chars=1000,
                placeholder="Enter review notes...",
            )

            col_approve, col_reject = st.columns(2)

            with col_approve:
                approve_clicked = st.form_submit_button(
                    "Approve Quotation",
                    type="primary",
                    use_container_width=True,
                )

            with col_reject:
                reject_clicked = st.form_submit_button(
                    "Reject Quotation",
                    use_container_width=True,
                )

        if approve_clicked or reject_clicked:
            if not reviewer_name.strip():
                st.error("Please enter the reviewer name.")

            else:
                decision = (
                    "approved" if approve_clicked else "rejected"
                )

                review_payload = {
                    "quotation_id": quotation.get("quotation_id"),
                    "decision": decision,
                    "reviewer": reviewer_name.strip(),
                    "notes": review_notes.strip(),
                }

                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/quotation/review",
                        json=review_payload,
                        timeout=15,
                    )

                    try:
                        review_data = response.json()
                    except ValueError:
                        review_data = {}

                    if response.ok and review_data.get("success"):
                        quotation["status"] = review_data["status"]
                        quotation["review_message"] = review_data.get(
                            "message",
                            "Review decision saved successfully.",
                        )
                        quotation["reviewer"] = reviewer_name.strip()

                        st.rerun()

                    else:
                        st.error(
                            review_data.get(
                                "message",
                                f"Review failed. HTTP {response.status_code}.",
                            )
                        )

                except requests.RequestException:
                    st.error(
                        "Could not connect to the API. "
                        "Check that the API server is running."
                    )
