import unittest
from rag_answer import answer_business_question


class TestRAGAnswers(unittest.TestCase):

    # 1. Test individual product facts
    def test_standard_tractor_trailer(self):
        answer = answer_business_question(
            "What is the capacity and base price of the Standard Tractor Trailer?"
        )
        self.assertIn("5.0 tons", answer)
        self.assertIn("₹185,000", answer)

    def test_hydraulic_trailer(self):
        answer = answer_business_question(
            "What is the capacity and base price of the Hydraulic Trailer?"
        )
        self.assertIn("8.0 tons", answer)
        self.assertIn("₹275,000", answer)

    def test_heavy_duty_trailer(self):
        answer = answer_business_question(
            "What is the capacity and base price of the Heavy Duty Trailer?"
        )
        self.assertIn("12.0 tons", answer)
        self.assertIn("₹425,000", answer)

    def test_agriculture_trailer_pro(self):
        answer = answer_business_question(
            "What is the capacity and base price of the Agriculture Trailer Pro?"
        )
        self.assertIn("7.0 tons", answer)
        self.assertIn("₹235,000", answer)

    def test_custom_trailer(self):
        answer = answer_business_question(
            "What is the capacity and base price of the Custom Trailer?"
        )
        self.assertIn("10.0 tons", answer)
        self.assertIn("₹350,000", answer)

    # 2. Test product comparison
    def test_product_comparison(self):
        answer = answer_business_question(
            "Compare the Hydraulic Trailer and Heavy Duty Trailer "
            "capacities and base prices."
        )
        self.assertIn("Hydraulic Trailer", answer)
        self.assertIn("Heavy Duty Trailer", answer)
        self.assertIn("₹275,000", answer)
        self.assertIn("₹425,000", answer)

    # 3. Test lowest and highest prices
    def test_lowest_base_price(self):
        answer = answer_business_question(
            "Which catalog product has the lowest base price?"
        )
        self.assertIn("Standard Tractor Trailer", answer)
        self.assertIn("₹185,000", answer)

    def test_highest_base_price(self):
        answer = answer_business_question(
            "Which catalog product has the highest base price?"
        )
        self.assertIn("Heavy Duty Trailer", answer)
        self.assertIn("₹425,000", answer)

    # 4. Test product recommendations
    def test_general_agricultural_transportation(self):
        answer = answer_business_question(
            "Which trailer is suitable for general agricultural transportation?"
        )
        self.assertIn("Standard Tractor Trailer", answer)

    def test_high_load_applications(self):
        answer = answer_business_question(
            "Which trailer is designed for high-load agricultural "
            "and transport applications?"
        )
        self.assertIn("Heavy Duty Trailer", answer)

    def test_agriculture_trailer_pro_recommended_uses(self):
        answer = answer_business_question(
            "What are the recommended uses of the Agriculture Trailer Pro?"
        )

        self.assertIn("Agriculture Trailer Pro", answer)
        self.assertIn("transportation", answer.lower())
        self.assertIn("crop", answer.lower())

    # Test that unsupported facts are not invented
    def test_unknown_product_specification(self):
        answer = answer_business_question(
            "What is the engine horsepower of the Hydraulic Trailer?"
        )

        answer_lower = answer.lower()

        expected_phrases = [
            "not specified",
            "does not provide",
            "doesn't specify",
            "not available",
            "insufficient information",
            "cannot determine",
            "not mentioned",
        ]

        self.assertTrue(
            any(phrase in answer_lower for phrase in expected_phrases),
            f"The answer did not clearly indicate missing information: {answer}"
        )

    # 5. Test warranty safeguards
    def test_warranty_duration(self):
        answer = answer_business_question(
            "What is the exact warranty duration?"
        )
        self.assertIn("not specified", answer.lower())

    def test_warranty_overloading(self):
        answer = answer_business_question(
            "Does warranty cover damage caused by overloading?"
        )
        self.assertIn("overloading", answer.lower())
        self.assertIn("does not automatically cover", answer.lower())

    def test_warranty_claim(self):
        answer = answer_business_question(
            "How can a customer make a warranty claim?"
        )
        self.assertIn("service team", answer.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)