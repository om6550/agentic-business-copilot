import json
import ollama

from schemas import BusinessAnswer


MODEL_NAME = "tinyllama"


def ask_llm(prompt):
    """Generate a normal text response."""
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


def ask_llm_structured(prompt):
    """Generate and validate a structured business answer."""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise business assistant. "
                    "Use only the supplied business context. "
                    "Check whether the context contains the requested information. "
                    "If the answer is present, answer directly and set "
                    "insufficient_information to false. "
                    "Set insufficient_information to true only if the context "
                    "does not answer the main question. "
                    "Never invent facts. "
                    "Return a response matching the required JSON schema."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        format=BusinessAnswer.model_json_schema(),
        options={
            "temperature": 0,
            "num_predict": 256
        }
    )

    raw_response = response["message"]["content"]

    data = json.loads(raw_response)
    validated = BusinessAnswer.model_validate(data)

    return validated

    
def ask_llm_structured_qwen(prompt, language="Gujarati"):
    """Generate a structured answer using Qwen3 in the requested language."""

    response = ollama.chat(
        model="qwen3:0.6b",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a professional business assistant. "
                    f"Write the answer in {language}. "
                    "Use only the supplied business context. "
                    "Always include the relevant product or customer name "
                    "when available. "
                    "Preserve exact prices, quantities, capacities and names. "
                    "If the context answers the question, set "
                    "insufficient_information to false. "
                    "Never invent facts. "
                    "Do not explain your reasoning. "
                    "Return only data matching the required JSON schema."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        format=BusinessAnswer.model_json_schema(),
        options={
            "temperature": 0,
            "num_predict": 256
        }
    )

    raw_response = response["message"]["content"]

    validated = BusinessAnswer.model_validate_json(raw_response)

    return validated


if __name__ == "__main__":
    test_prompt = """
Business context:
The Hydraulic Trailer has a capacity of 8 tons.
Its base price is ₹275,000.

Question:
What is the price and capacity of the Hydraulic Trailer?
"""

    try:
        result = ask_llm_structured(test_prompt)

        print("\nSTRUCTURED RESPONSE:")
        print(result.model_dump_json(indent=2))

    except Exception as error:
        print("\nStructured response test failed:")
        print(type(error).__name__, error)
