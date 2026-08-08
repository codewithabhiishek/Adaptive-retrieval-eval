import os
import time
import random
import re
from dotenv import load_dotenv
import requests
from checker import answers_match

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

COT_PROMPT = """You are an expert mathematician.
Think step-by-step.
Write every reasoning step inside `<think> ... </think>` blocks.
When you are completely done, produce exactly one
<answer> your final answer </answer>
Nothing after `</answer>`."""

def parse_answer(content):
    if not content:
        return None
    match = re.search(r"<answer>(.*?)</answer>", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"<answer>\s*(.*)", content, re.DOTALL)
    if match:
        return match.group(1).strip().split("\n")[0].strip()
    boxed_matches = re.findall(r"\\boxed\{([^{}]*)\}", content)
    if boxed_matches:
        return boxed_matches[-1].strip()
    return None

def single_cot_call(problem_text, temperature=0.7, max_retries=5):
    retries = 0
    errors = []
    
    while retries <= max_retries:
        try:
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
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    ans = parse_answer(content)
                    return {
                        "raw_output": content,
                        "answer": ans,
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
        "raw_output": None,
        "answer": None,
        "retries": retries,
        "errors": errors,
        "status": "failed"
    }

def escalate_with_voting(problem_text, n_votes=5):
    all_raw = []
    answers = []
    total_retries = 0
    all_errors = []
    failed_calls = 0

    for i in range(n_votes):
        res = single_cot_call(problem_text)
        all_raw.append(res["raw_output"])
        answers.append(res["answer"])
        total_retries += res["retries"]
        all_errors.extend(res["errors"])
        if res["status"] == "failed":
            failed_calls += 1
            
        # Mild spacing between escalation calls to prevent sudden rate bursts
        time.sleep(1.5)

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
        return {
            "voted_answer": None,
            "all_votes": answers,
            "all_raw": all_raw,
            "retries": total_retries,
            "errors": all_errors,
            "failed_calls": failed_calls
        }

    majority_group = max(groups, key=len)
    final_answer = majority_group[0]
    
    return {
        "voted_answer": final_answer,
        "all_votes": answers,
        "all_raw": all_raw,
        "retries": total_retries,
        "errors": all_errors,
        "failed_calls": failed_calls
    }