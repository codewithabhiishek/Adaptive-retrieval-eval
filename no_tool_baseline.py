import os
import csv
import json
import time
import random
import argparse
from dotenv import load_dotenv
import requests
from datasets import load_dataset
from adaptive_agent import parse_answer
from checker import answers_match, clean_answer

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

RESULTS_DIR = "results"
OUTPUT_CSV = os.path.join(RESULTS_DIR, "no_tool_baseline_results.csv")
RAW_JSONL = os.path.join(RESULTS_DIR, "raw_no_tool_baseline.jsonl")

FIELDNAMES = [
    "problem_id",
    "difficulty",
    "problem_text",
    "model_answer",
    "ground_truth",
    "is_correct",
    "api_calls",
    "retries_and_errors",
    "status"
]

NO_TOOL_SYSTEM_PROMPT = """You are an expert mathematician.
Think step-by-step.
Write every reasoning step inside `<think> ... </think>` blocks.
When you are ready to give the final answer, use the <answer> tag like
this: <answer>your final answer</answer>"""

def call_groq_api_no_tool(problem_text, temperature=0.0, max_retries=5, max_tokens=1536):
    """
    Helper function to call Groq API with retries, max_tokens limit, and exponential backoff.
    """
    retries = 0
    errors = []
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": NO_TOOL_SYSTEM_PROMPT},
            {"role": "user", "content": problem_text}
        ]
    }

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
                    return {
                        "content": content,
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

def run_no_tool_baseline(limit=100, output_csv=OUTPUT_CSV, raw_jsonl=RAW_JSONL):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")
    subset = dataset.select(range(limit))
    
    completed_ids = load_existing_progress(output_csv)
    print(f"Loaded MATH-500 subset of {limit} problems. Already completed: {len(completed_ids)}")
    
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

        print(f"\n=== Running No-Tool Baseline Problem {problem_id + 1}/{limit} (Level {level}) ===")

        res = call_groq_api_no_tool(problem)
        
        if res["status"] == "failed":
            print(f"  -> API call failed for problem {problem_id}")
            row = {
                "problem_id": problem_id,
                "difficulty": level,
                "problem_text": problem[:100],
                "model_answer": None,
                "ground_truth": ground_truth,
                "is_correct": False,
                "api_calls": res["retries"],
                "retries_and_errors": json.dumps(res["errors"]),
                "status": "failed"
            }
            writer.writerow(row)
            csv_file.flush()
            continue

        raw_output = res["content"]
        model_answer = parse_answer(raw_output)
        is_correct = answers_match(model_answer, ground_truth) if model_answer else False
        
        print(f"  Path: no_tool_cot | Answer: {model_answer} | Truth: {ground_truth} | Correct: {is_correct}")

        row = {
            "problem_id": problem_id,
            "difficulty": level,
            "problem_text": problem[:100],
            "model_answer": model_answer,
            "ground_truth": ground_truth,
            "is_correct": is_correct,
            "api_calls": 1,
            "retries_and_errors": json.dumps({"retries": res["retries"], "errors": res["errors"]}),
            "status": "success"
        }
        
        writer.writerow(row)
        csv_file.flush()
        
        raw_log = {
            "problem_id": problem_id,
            "difficulty": level,
            "ground_truth": ground_truth,
            "raw_output": raw_output,
            "model_answer": model_answer,
            "is_correct": is_correct
        }
        jsonl_file.write(json.dumps(raw_log) + "\n")
        jsonl_file.flush()
        
        time.sleep(2)

    csv_file.close()
    jsonl_file.close()
    print(f"\nNo-Tool Baseline experiment run finished. Output saved to {output_csv} and {raw_jsonl}")

def generate_comparison_table():
    pilot_csv = os.path.join(RESULTS_DIR, "pilot_100_results.csv")
    no_tool_csv = OUTPUT_CSV
    output_md = "NO_TOOL_COMPARISON.md"

    if not os.path.exists(pilot_csv) or not os.path.exists(no_tool_csv):
        print("Required CSV files for comparison table not found yet.")
        return

    # Load pilot results (tool offered)
    pilot_data = {}
    with open(pilot_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lvl = r["difficulty"].replace("Level", "").strip()
            if lvl not in pilot_data:
                pilot_data[lvl] = {"n": 0, "correct": 0}
            pilot_data[lvl]["n"] += 1
            if r.get("initial_correct", "").lower() == "true":
                pilot_data[lvl]["correct"] += 1

    # Load no-tool baseline results
    no_tool_data = {}
    with open(no_tool_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lvl = r["difficulty"].replace("Level", "").strip()
            if lvl not in no_tool_data:
                no_tool_data[lvl] = {"n": 0, "correct": 0}
            no_tool_data[lvl]["n"] += 1
            if r.get("is_correct", "").lower() == "true":
                no_tool_data[lvl]["correct"] += 1

    sorted_levels = sorted(pilot_data.keys(), key=lambda x: int(x) if x.isdigit() else 999)

    md = """# No-Tool Baseline vs. Tool-Offered Accuracy Comparison

This table compares single-pass CoT accuracy across MATH-500 difficulty levels when the search tool is offered versus when no tool is mentioned.

| Difficulty Level | Sample Size ($n$) | Tool Offered Initial Accuracy (%) | No-Tool Baseline Accuracy (%) | Difference (pp) |
| :--- | :---: | :---: | :---: | :---: |
"""
    total_n_pilot = 0
    total_corr_pilot = 0
    total_n_notool = 0
    total_corr_notool = 0

    for lvl in sorted_levels:
        p_n = pilot_data[lvl]["n"]
        p_c = pilot_data[lvl]["correct"]
        nt_n = no_tool_data.get(lvl, {}).get("n", 0)
        nt_c = no_tool_data.get(lvl, {}).get("correct", 0)

        total_n_pilot += p_n
        total_corr_pilot += p_c
        total_n_notool += nt_n
        total_corr_notool += nt_c

        p_acc = (p_c / p_n * 100) if p_n > 0 else 0.0
        nt_acc = (nt_c / nt_n * 100) if nt_n > 0 else 0.0
        diff = nt_acc - p_acc

        sign = "+" if diff > 0 else ""
        md += f"| **Level {lvl}** | {p_n} | {p_acc:.1f}% ({p_c}/{p_n}) | {nt_acc:.1f}% ({nt_c}/{nt_n}) | {sign}{diff:.1f}pp |\n"

    overall_p_acc = (total_corr_pilot / total_n_pilot * 100) if total_n_pilot > 0 else 0.0
    overall_nt_acc = (total_corr_notool / total_n_notool * 100) if total_n_notool > 0 else 0.0
    overall_diff = overall_nt_acc - overall_p_acc
    sign_ov = "+" if overall_diff > 0 else ""

    md += f"| **Overall (Total)** | **{total_n_pilot}** | **{overall_p_acc:.1f}% ({total_corr_pilot}/{total_n_pilot})** | **{overall_nt_acc:.1f}% ({total_corr_notool}/{total_n_notool})** | **{sign_ov}{overall_diff:.1f}pp** |\n"

    with open(output_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Comparison markdown saved to {output_md}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run No-Tool Baseline Experiment on MATH-500")
    parser.add_argument("--limit", type=int, default=100, help="Number of problems to evaluate (default: 100)")
    parser.add_argument("--compare-only", action="store_true", help="Generate comparison markdown table only")
    args = parser.parse_args()

    if args.compare_only:
        generate_comparison_table()
    else:
        run_no_tool_baseline(limit=args.limit)
        generate_comparison_table()
