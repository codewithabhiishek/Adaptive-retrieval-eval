import random
from adaptive_agent import call_adaptive_agent
from checker import answers_match
import csv

random.seed(42)

def generate_problems(n=60):
    problems = []
    for _ in range(n):
        op = random.choice(["+", "-", "*", "/"])
        if op == "/":
            b = random.randint(1, 12)
            a = b * random.randint(1, 12)  # ensures clean division
        else:
            a = random.randint(1, 50)
            b = random.randint(1, 50)
        if op == "+":
            truth = a + b
            text = f"What is {a} + {b}?"
        elif op == "-":
            a, b = max(a, b), min(a, b)  # avoid negatives for simplicity
            truth = a - b
            text = f"What is {a} - {b}?"
        elif op == "*":
            truth = a * b
            text = f"What is {a} times {b}?"
        else:
            truth = a // b
            text = f"What is {a} divided by {b}?"
        problems.append((text, str(truth)))
    return problems

def run():
    problems = generate_problems(60)
    rows = []
    for problem, truth in problems:
        r = call_adaptive_agent(problem)
        correct = answers_match(r["answer"], truth)
        rows.append({
            "problem": problem,
            "wants_search": r["wants_search"],
            "answer": r["answer"],
            "truth": truth,
            "correct": correct
        })
        print(f"{problem} | search={r['wants_search']} | answer={r['answer']} | truth={truth} | correct={correct}")

    with open("calibration_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    no_search = [r for r in rows if not r["wants_search"]]
    search = [r for r in rows if r["wants_search"]]

    print(f"\nTotal: {len(rows)}")
    print(f"Searched: {len(search)} ({100*len(search)/len(rows):.0f}%)")
    if no_search:
        ns_correct = sum(r["correct"] for r in no_search)
        print(f"No-search accuracy: {ns_correct}/{len(no_search)} ({100*ns_correct/len(no_search):.0f}%)")
    if search:
        s_correct = sum(r["correct"] for r in search)
        print(f"Search accuracy: {s_correct}/{len(search)} ({100*s_correct/len(search):.0f}%)")

if __name__ == "__main__":
    run()