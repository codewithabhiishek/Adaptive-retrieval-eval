import os
import re
import time
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = """You are an expert mathematician.
Think step-by-step.
Write every reasoning step inside `<think> ... </think>` blocks.
If you need to look up a formula, definition, or problems, you can use the <search>
tool by writing a search query inside the <search> tag like this:
<search>your search query</search>
After retrieval, you may:
1. Use the information if helpful
2. Explicitly state "Retrieved information not helpful" and continue without it
After the search results are returned, continue your step-by-step thinking.
When you are ready to give the final answer, use the <answer> tag like
this: <answer>your final answer</answer>"""

def call_adaptive_agent(problem_text, temperature=0.0, retry=True):
    time.sleep(10)  # pace calls to avoid rate limits
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "llama-3.1-8b-instant",
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
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
            return call_adaptive_agent(problem_text, temperature, retry=False)
        return {"raw_output": "", "wants_search": False, "answer": None}

    content = data["choices"][0]["message"]["content"]
    wants_search = "<search>" in content

    # Try strict match first (opening + closing tag)
    answer_match = re.search(r"<answer>(.*?)</answer>", content, re.DOTALL)
    if answer_match:
        answer = answer_match.group(1).strip()
    else:
        # Fallback 1: opening tag with no closing tag
        fallback_match = re.search(r"<answer>\s*(.*)", content, re.DOTALL)
        if fallback_match:
            answer = fallback_match.group(1).strip().split("\n")[0].strip()
            print(f"WARNING: no closing </answer> tag, used fallback: '{answer}'")
        else:
            # Fallback 2: model used \boxed{} instead of <answer> tags
            boxed_matches = re.findall(r"\\boxed\{([^{}]*)\}", content)
            if boxed_matches:
                answer = boxed_matches[-1].strip()
                print(f"WARNING: no <answer> tag, used \\boxed fallback: '{answer}'")
            else:
                print("NO ANSWER TAG OR BOXED ANSWER FOUND.")
                answer = None

    return {
        "raw_output": content,
        "wants_search": wants_search,
        "answer": answer
    }

# Quick manual test
if __name__ == "__main__":
    from datasets import load_dataset
    dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")

    test_problem = dataset[0]["problem"]
    print("PROBLEM:", test_problem)
    print("\n--- Calling model ---\n")

    result = call_adaptive_agent(test_problem)
    print("WANTS SEARCH:", result["wants_search"])
    print("EXTRACTED ANSWER:", result["answer"])
    print("\n--- RAW OUTPUT ---\n")
    print(result["raw_output"])