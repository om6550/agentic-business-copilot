
import json
import urllib.request
import urllib.error

from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from workflows import prepare_quotation_draft, review_quotation
from tools import (
    add_customer,
    get_customers,
    get_customer_profile,
    get_customer_quotation_history
)


HOST = "127.0.0.1"
PORT = 8000
MAX_REQUEST_SIZE = 10_000

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/prepare-quotation"


class BusinessCopilotHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):
        response = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    # --------------------------------------------------
    # GET ENDPOINTS
    # --------------------------------------------------

    def do_GET(self):

        path_info = urlparse(self.path)
        path = path_info.path

        # ----------------------------------------
        # 1. HEALTH CHECK
        # ----------------------------------------

        if path == "/health":

            self.send_json(200, {
                "success": True,
                "service": "Business Copilot API",
                "status": "running"
            })

        # ----------------------------------------
        # 2. CUSTOMER DIRECTORY
        # ----------------------------------------

        elif path == "/customers":

            query_params = parse_qs(path_info.query)

            status = query_params.get("status", [None])[0]
            search = query_params.get("search", [None])[0]

            result = get_customers(
                status=status,
                search=search
            )

            self.send_json(
                200 if result.get("success") else 500,
                result
            )

        # ----------------------------------------
        # 3. CUSTOMER PROFILE
        # GET /customers/7
        # ----------------------------------------

        elif path.startswith("/customers/"):

            path_parts = path.strip("/").split("/")

            # Validate customer ID.
            if len(path_parts) < 2 or not path_parts[1].isdigit():

                self.send_json(400, {
                    "success": False,
                    "message": "A valid customer ID is required."
                })
                return

            customer_id = int(path_parts[1])

            # ------------------------------------
            # 4. CUSTOMER QUOTATION HISTORY
            # GET /customers/7/quotations
            # ------------------------------------

            if len(path_parts) == 3 and path_parts[2] == "quotations":

                result = get_customer_quotation_history(customer_id)

            # ------------------------------------
            # CUSTOMER PROFILE
            # ------------------------------------

            elif len(path_parts) == 2:

                result = get_customer_profile(customer_id)

            else:

                self.send_json(404, {
                    "success": False,
                    "message": "Endpoint not found."
                })
                return

            # Return the appropriate HTTP status.
            if result.get("success"):

                status_code = 200

            elif result.get("not_found"):

                status_code = 404

            else:

                status_code = 500

            self.send_json(status_code, result)

        # ----------------------------------------
        # UNKNOWN ENDPOINT
        # ----------------------------------------

        else:

            self.send_json(404, {
                "success": False,
                "message": "Endpoint not found."
            })
    # --------------------------------------------------
    # POST ENDPOINTS
    # --------------------------------------------------

    def do_POST(self):

        path = urlparse(self.path).path

        allowed_endpoints = (
            "/customers",
            "/quotation",
            "/quotation/review",
            "/quotation/automate",
        )

        if path not in allowed_endpoints:

            self.send_json(404, {
                "success": False,
                "message": "Endpoint not found."
            })
            return

        try:

            # Read and validate request size

            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            if content_length <= 0 or content_length > MAX_REQUEST_SIZE:

                self.send_json(400, {
                    "success": False,
                    "message": "Invalid request size."
                })
                return

            # Read JSON request

            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body.decode("utf-8"))

            if not isinstance(data, dict):
                raise ValueError(
                    "The request must be a JSON object."
                )

            # --------------------------------------------------
            # 1. CUSTOMER REGISTRATION
            # --------------------------------------------------

            if path == "/customers":

                name = data.get("name")
                phone = data.get("phone")

                optional_fields = (
                    "company",
                    "city",
                    "customer_type",
                    "interested_product",
                )

                for field in optional_fields:

                    value = data.get(field, "")

                    if value is not None and not isinstance(value, str):
                        raise ValueError(
                            f"{field} must be text."
                        )

                if not isinstance(name, str) or not name.strip():
                    raise ValueError(
                        "Customer name is required."
                    )

                if not isinstance(phone, str) or not phone.strip():
                    raise ValueError(
                        "Customer phone number is required."
                    )

                result = add_customer(
                    name=name,
                    phone=phone,
                    company=data.get("company", ""),
                    city=data.get("city", ""),
                    customer_type=data.get("customer_type", ""),
                    interested_product=data.get(
                        "interested_product", ""
                    ),
                )

                self.send_json(
                    201 if result.get("success") else 400,
                    result
                )
                return

            # --------------------------------------------------
            # 2. QUOTATION AUTOMATION THROUGH N8N
            # --------------------------------------------------

            elif path == "/quotation/automate":

                customer_name = data.get("customer_name")
                product_name = data.get("product_name")
                quantity = data.get("quantity")

                if not isinstance(customer_name, str) or not customer_name.strip():
                    raise ValueError(
                        "A customer_name is required."
                    )

                if not isinstance(product_name, str) or not product_name.strip():
                    raise ValueError(
                        "A product_name is required."
                    )

                if (
                    isinstance(quantity, bool)
                    or not isinstance(quantity, int)
                    or quantity <= 0
                ):
                    raise ValueError(
                        "Quantity must be a positive whole number."
                    )

                payload = json.dumps({
                    "customer_name": customer_name.strip(),
                    "product_name": product_name.strip(),
                    "quantity": quantity
                }).encode("utf-8")

                n8n_request = urllib.request.Request(
                    N8N_WEBHOOK_URL,
                    data=payload,
                    headers={
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )

                try:

                    with urllib.request.urlopen(
                        n8n_request,
                        timeout=60
                    ) as response:

                        response_data = response.read().decode(
                            "utf-8"
                        )

                        try:
                            result = json.loads(response_data)

                        except json.JSONDecodeError:
                            result = {
                                "success": True,
                                "result": response_data
                            }

                        self.send_json(response.status, result)
                        return

                except urllib.error.HTTPError as error:

                    error_body = error.read().decode(
                        "utf-8",
                        errors="replace"
                    )

                    self.send_json(502, {
                        "success": False,
                        "message": "n8n workflow returned an HTTP error.",
                        "details": error_body
                    })
                    return

                except urllib.error.URLError as error:

                    self.send_json(502, {
                        "success": False,
                        "message": "Could not connect to the n8n webhook.",
                        "details": str(error.reason)
                    })
                    return

            # --------------------------------------------------
            # 3. DIRECT QUOTATION DRAFT
            # --------------------------------------------------

            elif path == "/quotation":

                customer_name = data.get("customer_name")
                product_name = data.get("product_name")
                quantity = data.get("quantity")

                if not isinstance(customer_name, str) or not customer_name.strip():
                    raise ValueError(
                        "A customer_name is required."
                    )

                if not isinstance(product_name, str) or not product_name.strip():
                    raise ValueError(
                        "A product_name is required."
                    )

                if (
                    isinstance(quantity, bool)
                    or not isinstance(quantity, int)
                ):
                    raise ValueError(
                        "Quantity must be a whole number."
                    )

                result = prepare_quotation_draft(
                    customer_name,
                    product_name,
                    quantity
                )

            # --------------------------------------------------
            # 4. QUOTATION APPROVAL / REJECTION
            # --------------------------------------------------

            elif path == "/quotation/review":

                quotation_id = data.get("quotation_id")
                decision = data.get("decision")
                reviewer = data.get("reviewer")
                notes = data.get("notes")

                if (
                    isinstance(quotation_id, bool)
                    or not isinstance(quotation_id, int)
                ):
                    raise ValueError(
                        "quotation_id must be an integer."
                    )

                result = review_quotation(
                    quotation_id=quotation_id,
                    decision=decision,
                    reviewer=reviewer,
                    notes=notes
                )

            else:

                self.send_json(404, {
                    "success": False,
                    "message": "Endpoint not found."
                })
                return

            self.send_json(
                200 if result.get("success") else 400,
                result
            )

        except (
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError
        ) as error:

            self.send_json(400, {
                "success": False,
                "message": str(error)
            })

        except Exception as error:

            print(f"[API ERROR] {error}")

            self.send_json(500, {
                "success": False,
                "message": (
                    "The business workflow encountered an internal error."
                )
            })

    def log_message(self, format_string, *args):
        print(f"[API] {args[0]}")


# --------------------------------------------------
# START API SERVER
# --------------------------------------------------

if __name__ == "__main__":

    server = ThreadingHTTPServer(
        (HOST, PORT),
        BusinessCopilotHandler
    )

    print(f"Business Copilot API running at http://{HOST}:{PORT}")
    print("Health check: GET http://127.0.0.1:8000/health")
    print("Customer list: GET http://127.0.0.1:8000/customers")
    print("Customer registration: POST http://127.0.0.1:8000/customers")
    print("Quotation: POST http://127.0.0.1:8000/quotation")
    print("Review: POST http://127.0.0.1:8000/quotation/review")
    print("Automation: POST http://127.0.0.1:8000/quotation/automate")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nStopping Business Copilot API...")

    finally:
        server.server_close()
