from pydantic import BaseModel, Field, ConfigDict


class BusinessAnswer(BaseModel):
    """Validated response from the AI Business Copilot."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(
        min_length=1,
        description="The concise answer to the user's business question."
    )

    insufficient_information: bool = Field(
        description=(
            "True when the available business context "
            "does not contain enough information to answer."
        )
    )


if __name__ == "__main__":
    # Test valid structured data
    test_data = {
        "answer": (
            "The Hydraulic Trailer has an 8-ton capacity "
            "and a base price of ₹275,000."
        ),
        "insufficient_information": False
    }

    validated_answer = BusinessAnswer(**test_data)

    print("SCHEMA TEST PASSED")
    print(validated_answer.model_dump_json(indent=2))
