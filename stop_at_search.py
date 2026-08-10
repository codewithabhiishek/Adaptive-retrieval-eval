import os
import csv
import json
import time
import re
import random
import argparse
from dotenv import load_dotenv
import requests
from datasets import load_dataset
from adaptive_agent import SYSTEM_PROMPT, parse_answer
from checker import answers_match

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

RESULTS_DIR = "results"
OUTPUT_CSV = os.path.join(RESULTS_DIR, "stop_at_search_results.csv")
RAW_JSONL = os.path.join(RESULTS_DIR, "raw_stop_at_search.jsonl")

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
    "pre_stop_reasoning",
    "post_stop_continuation",
    "api_calls",
    "retries_and_errors",
    "status"
]

def detect_repetition_loop(text, min_phrase_len=30, max_repeats=3):
    if not text:
        return False
    pattern = re.compile(rf'(.{{{min_phrase_len},}}?)\1{{{max_repeats-1},}}', re.DOTALL)
    match = pattern.search(text)
    return bool(match)

def call_groq_api(messages, stop_sequences=None, temperature=0.0, max_retries=5, max_tokens=1536):
    """
    Helper function to call Groq API with retries, max token limit, and exponential backoff.
    """
    retries = 0
    errors = []
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages
    }
    if stop_sequences:
        payload["stop"] = stop_sequences

    while retries <= max_retries:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    content = choice["message"]["content"] or ""
                    finish_reason = choice.get("finish_reason", "")
                    return {
                        "content": content,
                        "finish_reason": finish_reason,
                        "retries": retries,
                        "errors": errors,
                        "status": "success"
                    }
                else:
                    errors.append(f"Malformed response structure: {data}")
            elif response.status_code in [429, 500, 502, 503, 504]:
                errors.append(f"HTTP {response.status_code}: {response.text}")
            else:
                errors.append(f"HTTP {response.status_code}: {response.text}")
                break
        except Exception as e:
            errors.append(f"Exception: {str(e)}")
            
        retries += 1
        if retries <= max_retries:
            backoff = (2 ** retries) * 2.5 + random.uniform(0.5, 2.0)
            time.sleep(backoff)
            
    return {
        "content": "",
        "finish_reason": "error",
        "retries": retries,
        "errors": errors,
        "status": "failed"
    }

def load_existing_progress(csv_path):
    completed_ids = set()
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "success":
                    completed_ids.add(int(row["problem_id"]))
    return completed_ids

def run_stop_at_search_experiment(limit=100, output_csv=OUTPUT_CSV, raw_jsonl=RAW_JSONL):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")
    subset = dataset.select(range(limit))
    
    completed_ids = load_existing_progress(output_csv)
    print(f"Loaded dataset subset of {limit} problems. Already completed: {len(completed_ids)}")
    
    file_exists = os.path.exists(output_csv)
    csv_file = open(output_csv, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
    if not file_exists:
        writer.writeheader()
        csv_file.flush()
        
    jsonl_file = open(raw_jsonl, "a", encoding="utf-8")

    total_run = 0
    total_searched = 0
    total_correct = 0

    for i, item in enumerate(subset):
        problem_id = i
        if problem_id in completed_ids:
            print(f"Skipping problem {problem_id} (already completed).")
            continue
            
        problem = item["problem"]
        ground_truth = item["answer"]
        level = item.get("level", "unknown")

        print(f"\n=== Running Stop-at-Search Problem {problem_id + 1}/{limit} (Level {level}) ===")

        # Turn 1: Pass problem with stop sequence </search>
        messages_turn1 = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": problem}
        ]
        res1 = call_groq_api(messages_turn1, stop_sequences=["</search>"])
        
        if res1["status"] == "failed":
            print(f"  -> Pass 1 failed for problem {problem_id}")
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
                "pre_stop_reasoning": "",
                "post_stop_continuation": "",
                "api_calls": res1["retries"],
                "retries_and_errors": json.dumps(res1["errors"]),
                "status": "failed"
            }
            writer.writerow(row)
            csv_file.flush()
            continue

        raw_turn1 = res1["content"]
        # Check if search tag was emitted or stop sequence was hit
        wants_search = ("<search>" in raw_turn1) or (res1["finish_reason"] == "stop" and "<search>" in raw_turn1)
        
        if wants_search:
            # Format pre-stop reasoning clearly ending with </search>
            pre_stop_reasoning = raw_turn1.strip()
            if not pre_stop_reasoning.endswith("</search>"):
                pre_stop_reasoning += "</search>"
                
            initial_answer = parse_answer(pre_stop_reasoning)
            initial_correct = answers_match(initial_answer, ground_truth) if initial_answer else False
            
            print(f"  -> Search triggered! Stopped at </search>. Resuming with NO retrieval content...")
            
            # Turn 2: Resume generation with empty retrieval signal
            messages_turn2 = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": problem},
                {"role": "assistant", "content": pre_stop_reasoning},
                {
                    "role": "user",
                    "content": (
                        "No external search results were retrieved. Continue your step-by-step reasoning "
                        "from where you left off and state your final answer in <answer>...</answer> tags."
                    )
                }
            ]
            
            res2 = call_groq_api(messages_turn2)
            post_stop_continuation = res2["content"]
            
            all_errors = res1["errors"] + res2["errors"]
            if detect_repetition_loop(post_stop_continuation):
                print("  -> Warning: Repetition loop detected in post-stop continuation.")
                all_errors.append("repetition_loop_detected")

            full_combined = pre_stop_reasoning + "\n" + post_stop_continuation
            final_answer = parse_answer(post_stop_continuation) or parse_answer(full_combined)
            final_correct = answers_match(final_answer, ground_truth) if final_answer else False
            
            api_calls = 2
            total_retries = res1["retries"] + res2["retries"]
            status = "success" if res2["status"] == "success" else "failed"
            
            print(f"  Path: search_stopped_and_resumed | Initial: {initial_answer} | Final: {final_answer} | Truth: {ground_truth} | Correct: {final_correct}")
        else:
            # No search triggered in Turn 1
            pre_stop_reasoning = raw_turn1
            post_stop_continuation = ""
            initial_answer = parse_answer(raw_turn1)
            final_answer = initial_answer
            initial_correct = answers_match(initial_answer, ground_truth) if initial_answer else False
            final_correct = initial_correct
            
            api_calls = 1
            total_retries = res1["retries"]
            all_errors = res1["errors"]
            status = "success"
            
            print(f"  Path: no_search | Initial/Final: {initial_answer} | Truth: {ground_truth} | Correct: {final_correct}")

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
            "pre_stop_reasoning": pre_stop_reasoning,
            "post_stop_continuation": post_stop_continuation,
            "api_calls": api_calls,
            "retries_and_errors": json.dumps({"retries": total_retries, "errors": all_errors}),
            "status": status
        }
        
        writer.writerow(row)
        csv_file.flush()
        
        raw_log = {
            "problem_id": problem_id,
            "difficulty": level,
            "ground_truth": ground_truth,
            "search_triggered": wants_search,
            "pre_stop_reasoning": pre_stop_reasoning,
            "post_stop_continuation": post_stop_continuation,
            "initial_answer": initial_answer,
            "final_answer": final_answer,
            "final_correct": final_correct
        }
        jsonl_file.write(json.dumps(raw_log) + "\n")
        jsonl_file.flush()
        
        time.sleep(2)

    csv_file.close()
    jsonl_file.close()
    print(f"\nStop-at-search experiment completed. Output saved to {output_csv} and {raw_jsonl}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Stop-at-</search> Experiment on MATH-500")
    parser.add_argument("--limit", type=int, default=100, help="Number of problems to evaluate (default: 100)")
    args = parser.parse_args()
    
    run_stop_at_search_experiment(limit=args.limit)
