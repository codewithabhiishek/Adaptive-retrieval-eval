import os
import re
import time
import random
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

def parse_answer(content):
    if not content:
        return None
    # Try strict match first (opening + closing tag)
    answer_match = re.search(r"<answer>(.*?)</answer>", content, re.DOTALL)
    if answer_match:
        return answer_match.group(1).strip()
    
    # Fallback 1: opening tag with no closing tag
    fallback_match = re.search(r"<answer>\s*(.*)", content, re.DOTALL)
    if fallback_match:
        answer = fallback_match.group(1).strip().split("\n")[0].strip()
        return answer
    
    # Fallback 2: model used \boxed{} instead of <answer> tags
    boxed_matches = re.findall(r"\\boxed\{([^{}]*)\}", content)
    if boxed_matches:
        return boxed_matches[-1].strip()
        
    return None

def call_adaptive_agent(problem_text, temperature=0.0, max_retries=5):
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
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": problem_text}
                    ]
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    wants_search = "<search>" in content
                    answer = parse_answer(content)
                    return {
                        "raw_output": content,
                        "wants_search": wants_search,
                        "answer": answer,
                        "retries": retries,
                        "errors": errors,
                        "status": "success"
                    }
                else:
                    err_msg = f"Malformed response structure: {data}"
                    errors.append(err_msg)
            elif response.status_code in [429, 500, 502, 503, 504]:
                err_msg = f"HTTP {response.status_code}: {response.text}"
                errors.append(err_msg)
            else:
                err_msg = f"HTTP {response.status_code}: {response.text}"
                errors.append(err_msg)
                # Unrecoverable client error
                break
        except Exception as e:
            err_msg = f"Exception: {str(e)}"
            errors.append(err_msg)
            
        retries += 1
        if retries <= max_retries:
            # Exponential backoff with jitter (e.g. 5s, 10s, 20s, 40s...)
            backoff = (2 ** retries) * 2.5 + random.uniform(0.5, 2.0)
            time.sleep(backoff)
            
    return {
        "raw_output": None,
        "wants_search": False,
        "answer": None,
        "retries": retries,
        "errors": errors,
        "status": "failed"
    }