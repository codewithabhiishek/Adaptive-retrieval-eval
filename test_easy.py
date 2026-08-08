from adaptive_agent import call_adaptive_agent

# Deliberately trivial problems - if the model searches on these,
# it confirms the router isn't discriminating by difficulty at all
easy_problems = [
    "What is 2 + 2?",
    "What is 10 times 5?",
    "Simplify: 3/6",
    "What is the square root of 9?",
    "Solve for x: x + 1 = 2"
]

for i, problem in enumerate(easy_problems):
    print(f"\n=== Easy Problem {i+1}: {problem} ===")
    result = call_adaptive_agent(problem)
    print(f"WANTS SEARCH: {result['wants_search']}")
    print(f"ANSWER: {result['answer']}")