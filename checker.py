import re
from sympy import sympify, simplify, N
from sympy.parsing.latex import parse_latex

def clean_answer(ans):
    if ans is None:
        return ""
    ans = ans.strip()
    ans = ans.replace("\\left", "").replace("\\right", "")
    ans = ans.replace("$", "")
    ans = ans.replace("\\!", "")
    ans = ans.replace("\\pi", "pi").replace("π", "pi")
    return ans.strip()

def try_parse(ans):
    ans = clean_answer(ans)
    # Try LaTeX parsing first
    try:
        return parse_latex(ans)
    except Exception:
        pass
    # Try plain sympify as fallback
    try:
        return sympify(ans)
    except Exception:
        return None

def answers_match(model_answer, ground_truth):
    if model_answer is None:
        return False

    # 1. Try exact string match after cleaning (catches most cases, fast)
    a = clean_answer(model_answer).replace(" ", "")
    b = clean_answer(ground_truth).replace(" ", "")
    if a == b:
        return True

    # 2. Try symbolic comparison
    parsed_a = try_parse(model_answer)
    parsed_b = try_parse(ground_truth)

    if parsed_a is not None and parsed_b is not None:
        try:
            diff = simplify(parsed_a - parsed_b)
            if diff == 0:
                return True
        except Exception:
            pass
        try:
            if abs(N(parsed_a) - N(parsed_b)) < 1e-6:
                return True
        except Exception:
            pass

    return False

# Manual tests
if __name__ == "__main__":
    test_cases = [
        ("1/2", "0.5", True),
        ("\\frac{1}{2}", "0.5", True),
        ("3", "4", False),
        ("(3, pi/2)", "( 3, pi/2 )", True),
        ("p - q", "p-q", True),
    ]
    for model_ans, truth, expected in test_cases:
        result = answers_match(model_ans, truth)
        print(f"model='{model_ans}' truth='{truth}' -> match={result} (expected={expected})")