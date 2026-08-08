import os
import time
from collections import Counter
from dotenv import load_dotenv
import requests
import re
from checker import answers_match

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

COT_PROMPT = """You are an expert mathematician.
Think step-by-step.
Write every reasoning step inside `<think> ... </think>` blocks.
When you are completely done, produce exactly one
<answer> your final answer </answer>
Nothing after `</answer>`."""

def single_cot_call(problem_text, temperature=0.7, retry=True):
    time.sleep(10)  # pace every call, not just after errors
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "llama-3.1-8b-instant",
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": COT_PROMPT},
                {"role": "user", "content": problem_text}
            ]
        }
    )
    data = response.json()
    if "choices" not in data:
        print("API ERROR RESPONSE:", data)
        if retry:
            print("Backing off 30s and retrying once...")
            time.sleep(30)
            return single_cot_call(problem_text, temperature, retry=False)
        return None
    content = data["choices"][0]["message"]["content"]

    # Try strict match first (opening + closing tag)
    match = re.search(r"<answer>(.*?)</answer>", content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback 1: opening tag with no closing tag
    match = re.search(r"<answer>\s*(.*)", content, re.DOTALL)
    if match:
        fallback_answer = match.group(1).strip().split("\n")[0].strip()
        print(f"WARNING: no closing </answer> tag, used fallback: '{fallback_answer}'")
        return fallback_answer

    # Fallback 2: model used \boxed{} instead of <answer> tags
    boxed_matches = re.findall(r"\\boxed\{([^{}]*)\}", content)
    if boxed_matches:
        fallback_answer = boxed_matches[-1].strip()  # take the LAST boxed answer
        print(f"WARNING: no <answer> tag, used \\boxed fallback: '{fallback_answer}'")
        return fallback_answer

    print("NO ANSWER TAG OR BOXED ANSWER FOUND. Raw output was:")
    print(content)
    print("---")
    return None

def escalate_with_voting(problem_text, n_votes=5):
    answers = []
    for i in range(n_votes):
        ans = single_cot_call(problem_text)
        answers.append(ans)

    # Group answers that are mathematically equivalent
    groups = []
    for ans in answers:
        if ans is None:
            continue
        placed = False
        for group in groups:
            if answers_match(ans, group[0]):
                group.append(ans)
                placed = True
                break
        if not placed:
            groups.append([ans])

    if not groups:
        return None, answers

    majority_group = max(groups, key=len)
    final_answer = majority_group[0]
    return final_answer, answers

# Quick manual test
if __name__ == "__main__":
    from datasets import load_dataset
    dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")

    test_problem = dataset[1]["problem"]  # the harder Level 5 one
    print("PROBLEM:", test_problem)
    print("\n--- Running 5-vote escalation ---\n")

    final, all_answers = escalate_with_voting(test_problem)
    print("ALL 5 ANSWERS:", all_answers)
    print("MAJORITY ANSWER:", final)
    print("GROUND TRUTH:", dataset[1]["answer"])