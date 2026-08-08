from adaptive_agent import call_adaptive_agent
from checker import answers_match

# (problem, correct_answer) pairs - simple, unambiguous arithmetic
test_set = [
    ("What is 2 + 2?", "4"),
    ("What is 7 + 8?", "15"),
    ("What is 12 - 5?", "7"),
    ("What is 6 times 7?", "42"),
    ("What is 100 divided by 4?", "25"),
    ("What is 9 + 9?", "18"),
    ("What is 15 - 6?", "9"),
    ("What is 3 times 8?", "24"),
    ("What is 20 divided by 5?", "4"),
    ("What is 11 + 14?", "25"),
]

results = []
for problem, truth in test_set:
    r = call_adaptive_agent(problem)
    correct = answers_match(r["answer"], truth)
    results.append((problem, r["wants_search"], r["answer"], truth, correct))
    print(f"{problem} | search={r['wants_search']} | answer={r['answer']} | truth={truth} | correct={correct}")

no_search = [r for r in results if not r[1]]
if no_search:
    ns_correct = sum(r[4] for r in no_search)
    print(f"\nNo-search subset: {len(no_search)} problems, {ns_correct} correct ({100*ns_correct/len(no_search):.0f}%)")
else:
    print("\nModel searched on every single problem - zero no-search baseline to evaluate.")