import os
import csv
import json
import time
from datasets import load_dataset
from adaptive_agent import call_adaptive_agent
from escalate import escalate_with_voting
from checker import answers_match

# --- CONFIG ---
RESULTS_DIR = "results"
OUTPUT_CSV = os.path.join(RESULTS_DIR, "pilot_100_results.csv")
RAW_JSONL = os.path.join(RESULTS_DIR, "raw_outputs.jsonl")

FIELDNAMES = [
    "problem_id",
    "difficulty",
    "problem_text",
    "search_triggered",
    "initial_answer",
    "final_answer",
    "ground_truth",
    "initial_correct",
    "final_correct",
    "api_calls",
    "retries_and_errors",
    "status"
]

def load_existing_progress():
    completed_ids = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "success":
                    completed_ids.add(int(row["problem_id"]))
    return completed_ids

def run_pipeline(limit=100, output_csv=OUTPUT_CSV, raw_jsonl=RAW_JSONL):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Load MATH-500 test set (fixed deterministic ordering)
    dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")
    subset = dataset.select(range(limit))
    
    completed_ids = load_existing_progress()
    print(f"Loaded dataset subset of {limit} problems. Already completed: {len(completed_ids)}")
    
    # Ensure CSV header exists
    file_exists = os.path.exists(output_csv)
    csv_file = open(output_csv, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
    if not file_exists:
        writer.writeheader()
        csv_file.flush()
        
    jsonl_file = open(raw_jsonl, "a", encoding="utf-8")

    for i, item in enumerate(subset):
        problem_id = i
        if problem_id in completed_ids:
            print(f"Skipping problem {problem_id} (already completed).")
            continue
            
        problem = item["problem"]
        ground_truth = item["answer"]
        level = item.get("level", "unknown")

        print(f"\n=== Running Problem {problem_id + 1}/{limit} (Level {level}) ===")

        # Step 1: router call
        router_res = call_adaptive_agent(problem)
        
        if router_res["status"] == "failed":
            print(f"  -> Router call failed for problem {problem_id}")
            row = {
                "problem_id": problem_id,
                "difficulty": level,
                "problem_text": problem[:100],
                "search_triggered": False,
                "initial_answer": None,
                "final_answer": None,
                "ground_truth": ground_truth,
                "initial_correct": False,
                "final_correct": False,
                "api_calls": router_res["retries"],
                "retries_and_errors": json.dumps(router_res["errors"]),
                "status": "failed"
            }
            writer.writerow(row)
            csv_file.flush()
            continue

        wants_search = router_res["wants_search"]
        initial_answer = router_res["answer"]
        initial_correct = answers_match(initial_answer, ground_truth) if initial_answer is not None else False
        
        raw_log = {
            "problem_id": problem_id,
            "difficulty": level,
            "ground_truth": ground_truth,
            "router_output": router_res["raw_output"],
            "search_triggered": wants_search,
            "initial_answer": initial_answer,
            "initial_correct": initial_correct,
            "escalation_outputs": []
        }

        if not wants_search:
            # Fast path
            final_answer = initial_answer
            final_correct = initial_correct
            api_calls = 1
            total_retries = router_res["retries"]
            all_errors = router_res["errors"]
            status = "success"
            print(f"  Path: no_search | Initial/Final: {initial_answer} | Truth: {ground_truth} | Correct: {final_correct}")
        else:
            # Escalation path
            print("  -> Search triggered, escalating with 5-vote CoT...")
            esc_res = escalate_with_voting(problem, n_votes=5)
            
            raw_log["escalation_outputs"] = esc_res["all_raw"]
            final_answer = esc_res["voted_answer"]
            final_correct = answers_match(final_answer, ground_truth) if final_answer is not None else False
            
            api_calls = 1 + (5 - esc_res["failed_calls"])
            total_retries = router_res["retries"] + esc_res["retries"]
            all_errors = router_res["errors"] + esc_res["errors"]
            status = "success" if esc_res["voted_answer"] is not None or esc_res["failed_calls"] < 5 else "failed"
            print(f"  Path: search_escalated | Initial: {initial_answer} (Correct: {initial_correct}) | Final: {final_answer} (Correct: {final_correct}) | Truth: {ground_truth}")

        row = {
            "problem_id": problem_id,
            "difficulty": level,
            "problem_text": problem[:100],
            "search_triggered": wants_search,
            "initial_answer": initial_answer,
            "final_answer": final_answer,
            "ground_truth": ground_truth,
            "initial_correct": initial_correct,
            "final_correct": final_correct,
            "api_calls": api_calls,
            "retries_and_errors": json.dumps({"retries": total_retries, "errors": all_errors}),
            "status": status
        }
        
        writer.writerow(row)
        csv_file.flush()
        
        jsonl_file.write(json.dumps(raw_log) + "\n")
        jsonl_file.flush()
        
        # Pacing to remain safely within Groq rate limits
        time.sleep(2)

    csv_file.close()
    jsonl_file.close()
    print(f"\nPipeline run completed. Output saved to {output_csv} and {raw_jsonl}")

if __name__ == "__main__":
    run_pipeline(limit=100)