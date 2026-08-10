# Case Studies: Illustrative Qualitative Examples (Pilot Run n=100)

This document contains key qualitative case studies extracted from `results/pilot_100_results.csv` and `results/raw_outputs.jsonl` to illustrate specific router & voting behavior.

---

## Category A: Fixed by Escalation Voting (Initial = Incorrect, Final = Correct)
Total occurrences in $n=100$ pilot: **20 problems** (+20.0% recovery rate)

### Example 1: Problem ID 5 (Level 2 Geometry)
* **Problem**: A regular hexagon can be divided into six equilateral triangles. If the perimeter of one triangle is 21 inches, what is the perimeter of the hexagon?
* **Initial Router Response**: `6 * 21 = 126 inches` (Incorrect logic: multiplied perimeters directly instead of finding side length first).
* **Initial Correctness**: `False`
* **Escalated Majority Vote**: 4 out of 5 calls correctly calculated side length $s = 21/3 = 7$ and perimeter $P = 6 \times 7 = 42$.
* **Final Voted Answer**: `42`
* **Final Correctness**: `True`

### Example 2: Problem ID 12 (Level 5 Number Theory)
* **Problem**: Finding proper divisors of integer $N = 284$.
* **Initial Router Response**: `64` (Incorrect candidate).
* **Initial Correctness**: `False`
* **Escalated Majority Vote**: Majority vote extracted and converged to `284`.
* **Final Voted Answer**: `284`
* **Final Correctness**: `True`

### Example 3: Problem ID 61 (Level 3 Algebra)
* **Problem**: Solve polynomial expansion $x^3 - x^2 + 3x - 6$.
* **Initial Router Response**: `x^3 - x^2 + 3x - 6` (Calculation error).
* **Initial Correctness**: `False`
* **Escalated Majority Vote**: Converged to `x^3 + 3x - 6`.
* **Final Voted Answer**: `x^3 + 3x - 6`
* **Final Correctness**: `True`

---

## Category B: Broken by Escalation Voting (Initial = Correct, Final = Incorrect)
Total occurrences in $n=100$ pilot: **3 problems** (Rare: only 3.0% of cases)

### Example 4: Problem ID 55 (Level 4 Trigonometry)
* **Problem**: Trigonometric simplification problem.
* **Initial Router Response**: `3`
* **Initial Correctness**: `True`
* **Escalated Majority Vote**: At higher temperature ($T=0.7$), 3 out of 5 reasoning paths hallucinated an extra step resulting in `4`.
* **Final Voted Answer**: `4`
* **Final Correctness**: `False`

### Example 5: Problem ID 24 (Level 5 Geometry)
* **Problem**: Coordinate geometry distance calculation.
* **Initial Router Response**: `10.0`
* **Initial Correctness**: `True`
* **Escalated Majority Vote**: Higher temperature sampling caused majority vote to drift to `6.5`.
* **Final Voted Answer**: `6.5`
* **Final Correctness**: `False`

---

## Category C: Search Over-Triggering on Easy Problems
### Example 6: Problem ID 17 (Level 1 Arithmetic)
* **Problem**: Compute $1 - 2 + 3 - 4 + 5 - \dots + 99 - 100$.
* **Search Triggered**: `True` (Emitted `<search>alternating sum formula</search>`).
* **Observation**: Model triggered retrieval tags for basic alternating sequence arithmetic despite knowing the answer directly (`-50`).
