"""Run the full CareBridge AI local demo pipeline."""
from generate_synthetic_data import main as generate
from ingest_pipeline import write_outputs
from ask_insights import answer_question


def main() -> None:
    generate()
    write_outputs()
    print("\nDemo Ask Insights checks:")
    for q in [
        "Which plan has the highest PBM spend?",
        "Show pharmacy spend by age group.",
        "Show me member names with diabetes.",
    ]:
        r = answer_question(q)
        print(f"- {q} -> {'Allowed' if r['allowed'] else 'Blocked'} | {r['answer']}")


if __name__ == "__main__":
    main()
