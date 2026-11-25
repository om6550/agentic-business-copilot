from llm import ask_llm_structured

from rag.search import search_knowledge

from tools import find_product


def answer_business_question(question, language="English"):
    """
    Answer a business question using:
    1. Direct SQLite product information when appropriate
    2. RAG business knowledge when document-based information is needed
    3. Structured LLM output for grounded answers
    4. Safety rules for warranty-related questions
    """

    gujarati_mixed = language == "Gujarati + English"

    print("\nSearching business knowledge...")

    # ---------------------------------------------------------
    # STEP 0: Normalize question and detect business intent
    # ---------------------------------------------------------

    question_lower = question.lower()

    # Multilingual warranty detection.
    # This MUST happen before RAG retrieval because warranty
    # questions should be restricted to the warranty policy
    # document.
    warranty_words = [
        "warranty",
        "warranties",
        "વોરંટી",
        "વારંટી",
        "waranti",
        "warrenty",
        "warrantee",
    ]

    asks_warranty = any(
        word in question_lower
        for word in warranty_words
    )

    sales_policy_words = [
        "sales policy",
        "payment",
        "payments",
        "advance",
        "booking",
        "financing",
        "finance",
        "loan",
        "delivery",
        "cancellation",
        "refund",
        "discount",
        "terms",
        "conditions",
        "bhugtan",
        "advance ketlo",
        "booking",
        "delivery ketli",
        "ડિલિવરી",
        "ચુકવણી",
        "એડવાન્સ",
        "લોન",
        "ફાઇનાન્સ",
    ]

    company_faq_words = [
        "company",
        "location",
        "address",
        "where are you",
        "where is",
        "contact",
        "phone",
        "office",
        "factory",
        "about company",
        "company information",
        "company ni mahiti",
        "location kya che",
        "address kya che",
        "કંપની",
        "સરનામું",
        "સ્થળ",
        "ફેક્ટરી",
        "સંપર્ક",
    ]

    product_catalog_words = [
        "product",
        "products",
        "trailer",
        "capacity",
        "specification",
        "specs",
        "model",
        "models",
        "product details",
        "product information",
        "ઉત્પાદન",
        "ટ્રેલર",
        "ક્ષમતા",
        "મોડેલ",
    ]

    asks_sales_policy = any(
        word in question_lower
        for word in sales_policy_words
    )

    asks_company_faq = any(
        word in question_lower
        for word in company_faq_words
    )

    asks_product_catalog = any(
        word in question_lower
        for word in product_catalog_words
    )

    # ---------------------------------------------------------
    # Handle high-load agricultural and transport questions.
    # ---------------------------------------------------------

    if (
        (
            "high-load" in question_lower
            or "high load" in question_lower
        )
        and (
            "agricultural" in question_lower
            or "transport" in question_lower
        )
    ):
        result = find_product("Heavy Duty Trailer")

        if result.get("success"):
            product = result["product"]

            return (
                f"{product['product_name']} is designed for high-load "
                "agricultural and transport applications."
            )

    # ---------------------------------------------------------
    # Handle general agricultural transportation questions.
    # ---------------------------------------------------------

    if (
        "general agricultural transportation" in question_lower
        and not any(
            term in question_lower
            for term in [
                "compare",
                "comparison",
                "price",
                "cost",
                "capacity",
            ]
        )
    ):
        result = find_product("Standard Tractor Trailer")

        if result.get("success"):
            product = result["product"]

            return (
                f"{product['product_name']} is designed for general "
                "agricultural transportation. It is suitable for "
                "transporting crops, farm materials, equipment, "
                "and other agricultural loads."
            )

    # ---------------------------------------------------------
    # Handle exact product price and capacity questions.
    # ---------------------------------------------------------

    asks_product_facts = (
        any(
            term in question_lower
            for term in [
                "price",
                "cost",
                "capacity",
                "how many tons",
                "base price",
            ]
        )
        and any(
            term in question_lower
            for term in [
                "trailer",
                "hydraulic",
                "heavy duty",
                "agriculture",
                "standard",
                "custom",
            ]
        )
        and not any(
            term in question_lower
            for term in [
                "compare",
                "comparison",
                "cheaper",
                "lowest",
                "highest",
            ]
        )
    )

    if asks_product_facts:

        product_names = [
            "Standard Tractor Trailer",
            "Hydraulic Trailer",
            "Heavy Duty Trailer",
            "Agriculture Trailer Pro",
            "Custom Trailer",
        ]

        matched_product = next(
            (
                name
                for name in product_names
                if name.lower() in question_lower
            ),
            None,
        )

        if matched_product:
            result = find_product(matched_product)

            if result.get("success"):
                product = result["product"]

                output = (
                    f"{product['product_name']} has a capacity of "
                    f"{product['capacity_tons']} tons and a base price of "
                    f"₹{product['base_price']:,.0f}."
                )

                if (
                    "description" in product
                    and product["description"]
                ):
                    output += f"\n{product['description']}"

                return output

    # ---------------------------------------------------------
    # Handle product comparisons and price rankings using SQLite.
    # ---------------------------------------------------------

    product_names = [
        "Standard Tractor Trailer",
        "Hydraulic Trailer",
        "Heavy Duty Trailer",
        "Agriculture Trailer Pro",
        "Custom Trailer",
    ]

    # Check whether the question asks for the lowest price.
    asks_lowest_price = any(
        term in question_lower
        for term in [
            "lowest base price",
            "lowest price",
            "cheapest",
            "most affordable",
            "least expensive",
        ]
    )

    # Check whether the question asks for the highest price.
    asks_highest_price = any(
        term in question_lower
        for term in [
            "highest base price",
            "highest price",
            "most expensive",
            "costliest",
            "priciest",
        ]
    )

    # ---------------------------------------------------------
    # Find product with lowest/highest base price.
    # ---------------------------------------------------------

    if asks_lowest_price or asks_highest_price:

        products = []

        for name in product_names:
            result = find_product(name)

            if result.get("success"):
                products.append(result["product"])

        if products:

            if asks_lowest_price:
                selected_product = min(
                    products,
                    key=lambda product: product["base_price"],
                )

                ranking_label = "Lowest base price"

            else:
                selected_product = max(
                    products,
                    key=lambda product: product["base_price"],
                )

                ranking_label = "Highest base price"

            return (
                f"{ranking_label}: "
                f"{selected_product['product_name']} "
                f"has a base price of "
                f"₹{selected_product['base_price']:,.0f} "
                f"and a capacity of "
                f"{selected_product['capacity_tons']:g} tons."
            )

    # ---------------------------------------------------------
    # Handle comparisons between named products.
    # ---------------------------------------------------------

    asks_comparison = any(
        term in question_lower
        for term in [
            "compare",
            "comparison",
            "versus",
            "difference between",
            "cheaper",
        ]
    ) or " vs " in question_lower

    if asks_comparison:

        matched_products = []

        for name in product_names:

            if name.lower() in question_lower:

                result = find_product(name)

                if result.get("success"):
                    matched_products.append(
                        result["product"]
                    )

        if len(matched_products) >= 2:

            output_lines = [
                "Product comparison:"
            ]

            for product in matched_products:

                output_lines.append(
                    f"{product['product_name']}: "
                    f"{product['capacity_tons']:g} tons, "
                    f"base price ₹{product['base_price']:,.0f}."
                )

            output_lines.append(
                "Note: Base prices may vary with configuration "
                "and customization."
            )

            return "\n".join(output_lines)

    # =========================================================
    # STEP 1: Retrieve relevant business documents
    # =========================================================

    # IMPORTANT:
    #
    # Warranty detection is performed BEFORE retrieval.
    #
    # This allows English, Roman Gujarati, and Gujarati-script
    # warranty questions to use the warranty policy document.
    #
    # Examples:
    #   What is the warranty policy?
    #   Hydraulic Trailer ni warranty shu che?
    #   Hydraulic Trailer ni warranty ketli che?
    #   વોરંટી વિશે માહિતી આપો
    #
    # STEP 1: Retrieve relevant business documents

# ---------------------------------------------------------
# STEP 1: Topic-aware business document retrieval
# ---------------------------------------------------------

    if asks_warranty:

        results = search_knowledge(
            question,
            top_k=5,
            source="warranty_policy.txt",
            max_distance=None
        )

    elif asks_sales_policy:

       results = search_knowledge(
        question,
        top_k=2,
        source="sales_policy.txt",
        max_distance=1.1
    )

    elif asks_company_faq:

        results = search_knowledge(
            question,
            top_k=5,
            source="company_faq.txt",
            max_distance=None
        )

    elif asks_product_catalog:

        results = search_knowledge(
            question,
            top_k=5,
            source="product_catalog.txt",
            max_distance=None
        )

    else:

        results = search_knowledge(
            question,
            top_k=2,
            max_distance=1.0
        )

    # ---------------------------------------------------------
    # Validate search results.
    # ---------------------------------------------------------

    if not isinstance(results, tuple) or len(results) < 2:
        raise ValueError(
            "Unexpected format returned by RAG search."
        )

    documents, metadatas, distances = results

    print(
        "DEBUG - Retrieved distances:",
        [round(float(distance), 4) for distance in distances]
    )

    # ---------------------------------------------------------
    # STEP 2: Build context and collect sources.
    # ---------------------------------------------------------

    context_parts = []
    sources = []

    for index, content in enumerate(documents):

        if not content:
            continue

        context_parts.append(str(content))

        if index < len(metadatas):

            metadata = metadatas[index]

            if isinstance(metadata, dict):

                source = metadata.get("source")

                if source:
                    sources.append(str(source))

    if not context_parts:

        return (
            "I couldn't find sufficiently relevant information "
            "in the available business documents. "
            "Please ask about our products, pricing, inventory, "
            "warranty, sales policy, or company information."
        )

    context = "\n\n".join(context_parts)

        # ---------------------------------------------------------
    # Sales policy relevance check.
    # ---------------------------------------------------------

    if asks_sales_policy and "payment" in question_lower:

        payment_terms = [
            "payment",
            "advance",
            "booking",
            "financing",
            "finance",
            "loan",
            "bhugtan",
            "ચુકવણી",
            "એડવાન્સ",
        ]

        if not any(
            term in context.lower()
            for term in payment_terms
        ):
            return (
                "The current sales policy does not specify "
                "a payment policy."
            )

    print(
        f"Retrieved {len(context_parts)} document chunks."
    )

    print("\nDEBUG - CONTEXT:")
    print(context)

    # =========================================================
    # STEP 2.5: Warranty safety and policy handling
    # =========================================================

    # Safety rule:
    # Never let the LLM invent an exact warranty duration.

    asks_warranty_duration = (
        asks_warranty
        and any(
            term in question_lower
            for term in [
                # English
                "duration",
                "period",
                "how long",
                "how many years",
                "how many months",
                "exact warranty",
                "warranty last",
                "year",
                "month",

                # Roman Gujarati
                "ketli",
                "ketlo",
                
                "ketla",
                "ketli che",
                "ketla varsh",
                "ketla mahina",
                "varsh",
                "mahina",

                # Gujarati script
                "કેટલી",
                "કેટલો",
                "કેટલા",
                "વર્ષ",
                "મહિના",
                "મહિનો",
                "દિવસ",
            ]
        )
    )

    # ---------------------------------------------------------
    # Exact warranty duration question
    # ---------------------------------------------------------

    if asks_warranty_duration:

        if gujarati_mixed:

            output = (
                "Available policy મુજબ exact warranty duration "
                "જણાવેલી નથી. કૃપા કરીને company પાસેથી તેની "
                "પુષ્ટિ કરો. Warranty terms product configuration "
                "અને customer ના final quotation અથવા order "
                "પર આધારિત છે."
            )

        else:

            output = (
                "The exact warranty duration is not specified in the "
                "available policy. Please confirm it with the company. "
                "Warranty terms depend on the product configuration "
                "and the final terms in the customer's quotation or order."
            )

        unique_sources = list(dict.fromkeys(sources))

        if unique_sources:
            output += (
                "\n\nSources: "
                + ", ".join(unique_sources)
            )

        return output

    # ---------------------------------------------------------
    # Handle warranty coverage questions directly from policy.
    # ---------------------------------------------------------

    if asks_warranty:

        # ---------------------------------------------
        # Misuse / overloading / accident / maintenance
        # ---------------------------------------------

        if any(
            term in question_lower
            for term in [
                "overloading",
                "overload",
                "misuse",
                "accident",
                "improper maintenance",
                "unauthorized modification",
            ]
        ):

            if gujarati_mixed:

                output = (
                    "Warranty માં misuse, overloading, "
                    "unauthorized modification, accidents અથવા "
                    "improper maintenance ને કારણે થયેલું damage "
                    "automatically cover થતું નથી."
                )

            else:

                output = (
                    "The warranty policy does not automatically cover "
                    "damage caused by misuse, overloading, unauthorized "
                    "modification, accidents, or improper maintenance."
                )

            unique_sources = list(dict.fromkeys(sources))

            if unique_sources:
                output += (
                    "\n\nSources: "
                    + ", ".join(unique_sources)
                )

            return output

        # ---------------------------------------------
        # Warranty claim questions
        # ---------------------------------------------

        if any(
            term in question_lower
            for term in [
                "claim",
                "claims",
                "make a claim",
            ]
        ):

            if gujarati_mixed:

                output = (
                    "Available policy મુજબ exact warranty duration "
                    "જણાવેલી નથી. કૃપા કરીને company પાસેથી તેની "
                    "પુષ્ટિ કરો. Warranty terms product configuration "
                    "અને customer ના final quotation અથવા order "
                    "પર આધારિત છે."
                )

            else:

                output = (
                    "For warranty claims, customers should contact the company "
                    "service team."
                )

            unique_sources = list(dict.fromkeys(sources))

            if unique_sources:
                output += (
                    "\n\nSources: "
                    + ", ".join(unique_sources)
                )

            return output

        # ---------------------------------------------
        # General warranty policy response
        # ---------------------------------------------

        if gujarati_mixed:

            output = (
                "Warranty coverage product configuration અને "
                "customer ના final quotation અથવા order માં "
                "જણાવેલી terms પર આધારિત છે.\n\n"

                "Standard products માટે warranty coverage "
                "સંબંધિત order ની warranty terms મુજબ રહેશે. "
                "Customization ના કારણે warranty coverage માં "
                "ફેરફાર થઈ શકે છે.\n\n"

                "Misuse, overloading, unauthorized modification, "
                "accidents અથવા improper maintenance ને કારણે "
                "થયેલું damage automatically cover થતું નથી.\n\n"

                "Warranty claim માટે company service team નો "
                "સંપર્ક કરો.\n\n"

                "Available policy માં exact warranty duration "
                "જણાવેલી નથી. તેની પુષ્ટિ company પાસેથી કરવી."
            )

        else:

            output = (
                "Warranty coverage depends on the product configuration "
                "and the final terms specified in the customer's "
                "quotation or order.\n\n"

                "Standard products are covered according to the warranty "
                "terms applicable to the specific order. Customization "
                "may affect warranty coverage depending on the modification.\n\n"

                "Warranty does not automatically cover damage caused by "
                "misuse, overloading, unauthorized modification, accidents, "
                "or improper maintenance.\n\n"

                "For warranty claims, customers should contact the company "
                "service team.\n\n"

                "The exact warranty duration is not specified in the "
                "available policy and must be confirmed with the company."
            )

        unique_sources = list(dict.fromkeys(sources))

        if unique_sources:
            output += (
                "\n\nSources: "
                + ", ".join(unique_sources)
            )

        return 

    
        print("\nDEBUG - CONTEXT:")
        print(context)

    # =========================================================
    # STEP 3: Create a grounded LLM prompt
    # =========================================================

    prompt = f"""
Answer the user's question using only the business context below.

Business context:
{context}

User question:
{question}

Rules:
- Give the direct answer from the context.
- Do not invent information.
- If the context does not answer the question, set insufficient_information to true.
- If the context answers the question, set insufficient_information to false.
- Return only the required JSON response.
"""

    # =========================================================
    # STEP 4: Generate and validate structured output
    # =========================================================

    result = ask_llm_structured(prompt)

    output = result.answer

    if result.insufficient_information:

        output = (
            "The available business documents do not provide "
            "enough information to answer confidently.\n"
            + output
        )

    # ---------------------------------------------------------
    # Append unique source references.
    # ---------------------------------------------------------

    unique_sources = list(dict.fromkeys(sources))

    if unique_sources:

        output += (
            "\n\nSources: "
            + ", ".join(unique_sources)
        )

    return output


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    question = input(
        "Ask a business question: "
    ).strip()

    if not question:

        print("Please enter a question.")

    else:

        try:

            print("\nBUSINESS COPILOT ANSWER:")

            print(
                answer_business_question(question)
            )

        except Exception as error:

            print(
                "\nError while answering the question:"
            )

            print(
                type(error).__name__,
                error
            )
