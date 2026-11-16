"""
main.py

Command-line entry point. Run:
    python main.py
and type a medical claim or question at the prompt.
"""

from fact_checker import check_claim, BlockedResult


def print_result(result):
    print()
    if isinstance(result, BlockedResult):
        print(f"[blocked: {result.reason}]")
        print(result.message)
        return

    print(f"Verdict:     {result.verdict}")
    print(f"Confidence:  {result.confidence}")
    print(f"Explanation: {result.explanation}")
    if result.cited_pmids:
        print("Sources:")
        for s in result.sources:
            if s.pmid in result.cited_pmids:
                print(f"  - {s.as_citation()}")
    print()
    print(result.disclaimer)


def main():
    print("Medical fact-checker (Ctrl+C to quit)")
    print("Type a medical claim or question, e.g. 'does vitamin C prevent colds?'")
    while True:
        try:
            claim = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break
        if not claim:
            continue
        result = check_claim(claim)
        print_result(result)


if __name__ == "__main__":
    main()
