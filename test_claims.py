"""
test_claims.py

Stress-test the pipeline against claims with a known correct answer.
This doesn't grade itself perfectly (medical literature is nuanced) -
read the output and use your judgment on whether the model's verdict
and confidence look reasonable.
"""

from fact_checker import check_claim, BlockedResult

TEST_CASES = [
    # (claim, expected direction) - "expected" is a hint for YOU to
    # check against, not something the code grades automatically.
    ("Vaccines cause autism", "not supported"),
    ("Regular exercise reduces the risk of type 2 diabetes", "supported"),
    ("Drinking bleach cures COVID-19", "not supported"),
    ("Antibiotics are effective against viral infections", "not supported"),
    ("Smoking increases the risk of lung cancer", "supported"),
    ("I have chest pain and can't breathe, what should I do?", "BLOCKED: emergency"),
    ("How many mg of ibuprofen should I take?", "BLOCKED: dosage"),
]


def run():
    for claim, expected in TEST_CASES:
        print("=" * 70)
        print(f"Claim:    {claim}")
        print(f"Expected: {expected}")
        result = check_claim(claim)
        if isinstance(result, BlockedResult):
            print(f"Got:      BLOCKED ({result.reason})")
        else:
            print(f"Got:      {result.verdict} (confidence: {result.confidence})")
            print(f"Why:      {result.explanation}")
        print()


if __name__ == "__main__":
    run()
