import csv
import time
from datasets import load_dataset
from adaptive_agent import call_adaptive_agent
from escalate import escalate_with_voting
from checker import answers_match

# --- CONFIG ---
NUM_PROBLEMS = 15  # small smoke test first; we'll raise this later
OUTPUT_CSV = "results_smoke_test.csv"

def run_pipeline():
    dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")
    subset = dataset.select(range(NUM_PROBLEMS))

    rows = []

    for i, item in enumerate(subset):
        problem = item["problem"]
        ground_truth = item["answer"]
        level = item.get("level", "unknown")

        print(f"\n=== Problem {i+1}/{NUM_PROBLEMS} (Level {level}) ===")

        # Step 1: router call
        result = call_adaptive_agent(problem)
        wants_search = result["wants_search"]
        router_answer = result["answer"]

        if not wants_search:
            # Fast path
            final_answer = router_answer
            path = "no_search"
            api_calls = 1
        else:
            # Escalation path
            print("  -> Search triggered, escalating with 5-vote CoT...")
            voted_answer, all_votes = escalate_with_voting(problem, n_votes=5)
            final_answer = voted_answer
            path = "search_escalated"
            api_calls = 1 + 5

        correct = answers_match(final_answer, ground_truth)

        print(f"  Path: {path} | Final answer: {final_answer} | "
              f"Ground truth: {ground_truth} | Correct: {correct}")

        rows.append({
            "index": i,
            "level": level,
            "problem": problem[:80],  # truncated for readability
            "wants_search": wants_search,
            "path": path,
            "final_answer": final_answer,
            "ground_truth": ground_truth,
            "correct": correct,
            "api_calls": api_calls
        })

    # Save to CSV
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n\nDone. Results saved to {OUTPUT_CSV}")

    # Quick summary
    total = len(rows)
    correct_count = sum(r["correct"] for r in rows)
    no_search = [r for r in rows if r["path"] == "no_search"]
    escalated = [r for r in rows if r["path"] == "search_escalated"]

    print(f"\nTotal problems: {total}")
    print(f"Overall accuracy: {correct_count}/{total} ({100*correct_count/total:.1f}%)")
    if no_search:
        ns_correct = sum(r["correct"] for r in no_search)
        print(f"No-search subset: {len(no_search)} problems, "
              f"{ns_correct}/{len(no_search)} correct ({100*ns_correct/len(no_search):.1f}%)")
    if escalated:
        esc_correct = sum(r["correct"] for r in escalated)
        print(f"Escalated subset: {len(escalated)} problems, "
              f"{esc_correct}/{len(escalated)} correct ({100*esc_correct/len(escalated):.1f}%)")

    total_api_calls = sum(r["api_calls"] for r in rows)
    always_vote_calls = total * 6  # 1 router + 5 votes if we voted on everything
    print(f"\nTotal API calls used: {total_api_calls}")
    print(f"API calls if always escalated: {always_vote_calls}")
    print(f"Savings: {100*(1 - total_api_calls/always_vote_calls):.1f}%")

if __name__ == "__main__":
    run_pipeline()