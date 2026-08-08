# Adaptive Retrieval Router — Project Progress & Changelog

## 1. Project Milestone Overview

* **Goal**: Replicate and evaluate the metacognitive retrieval signal identified in *Adaptive Retrieval helps Reasoning in LLMs – but mostly if it's not used* (arXiv:2602.07213) on a hosted API inference setup (`llama-3.1-8b-instant` on Groq).
* **Current Status**: **Pilot Evaluation Complete ($n = 86$)**
* **Repository State**: Clean, structured, fully audited, and pushed to GitHub ([https://github.com/codewithabhiishek/adaptive-retrieval-eval](https://github.com/codewithabhiishek/adaptive-retrieval-eval)).

---

## 2. Progress Log & Completed Checklist

- [x] **Environment & API Setup**: Configured virtual environment (`venv`), installed `datasets`, `sympy`, `pandas`, `matplotlib`, and verified Groq API authentication.
- [x] **Core Agent Implementation (`adaptive_agent.py`)**: Prompts model with paper's exact system prompt (Appendix A.2.5), detects `<search>` tags, parses answers (with fallbacks for missing closing tags or `\boxed{}`).
- [x] **Symbolic Answer Checker (`checker.py`)**: Built `sympy`-based equivalence evaluator for fractions, decimals, algebraic terms, and pi expressions.
- [x] **Escalation Engine (`escalate.py`)**: Implemented 5-vote Self-Consistency Majority Vote sampling at $T=0.7$.
- [x] **Pipeline Orchestration (`pipeline.py`)**: Built main loop with exponential backoff retries on rate limits, checkpoint/resume capabilities, and secret scrubbing.
- [x] **Pilot Benchmark Execution**: Evaluated 86 MATH-500 problems ($n=86$).
- [x] **Data Logging & Auditing**:
  - Saved structured CSV to `results/pilot_100_results.csv`.
  - Saved full word-for-word raw reasoning logs to `results/raw_outputs.jsonl`.
- [x] **Visualization (`make_charts.py`)**: Rendered publication-grade PNG charts:
  - `charts/overall_accuracy.png` (Overall Initial vs. Escalated accuracy)
  - `charts/accuracy_by_level.png` (Accuracy grouped by Levels 1–5)
- [x] **Qualitative Analysis (`CASE_STUDIES.md`)**: Extracted illustrative examples of voting fixes, voting breaks, and tool over-triggering.
- [x] **Comparative Evaluation (`COMPARISON.md`)**: Documented side-by-side analysis of paper vs. API evaluation metrics.
- [x] **Repository Cleanup**: Relocated early exploratory/debug scripts into `scratch/` and verified `.gitignore` protection for secrets.

---

## 3. Key Quantitative Findings ($n = 86$ Pilot)

* **Search Trigger Rate**: **100.0% (84/84 successful)** — The model emitted `<search>` on every single problem.
* **No-Search Subset Count**: **0** (The "confident skip" signal did not occur in this setup).
* **Initial Single-Pass Accuracy**: **34.5% (29/84)**
* **Final 5-Vote Escalation Accuracy**: **52.4% (44/84)**
* **Net Escalation Gain**: **+17.9 percentage points**

### Breakdown by Difficulty Level (MATH-500)

| Difficulty | Sample Size ($n$) | Initial Pass | Final 5-Vote | Net Gain |
| :--- | :--- | :--- | :--- | :--- |
| **Level 1 (Easiest)** | 7 | 71.4% (5/7) | 71.4% (5/7) | +0.0pp |
| **Level 2** | 23 | 43.5% (10/23) | 65.2% (15/23) | **+21.7pp** |
| **Level 3** | 15 | 46.7% (7/15) | 80.0% (12/15) | **+33.3pp** |
| **Level 4** | 19 | 21.1% (4/19) | 42.1% (8/19) | **+21.0pp** |
| **Level 5 (Hardest)** | 20 | 15.0% (3/20) | 20.0% (4/20) | **+5.0pp** |

---

## 4. Next Steps & Future Milestones

- [ ] **Full 500-Problem Run**: Execute overnight `caffeinate` pipeline for all 500 MATH-500 problems.
- [ ] **Chart Re-generation**: Re-run `make_charts.py` on the final $n=500$ dataset to update PNGs.
- [ ] **Formal Research Paper Draft**: Write 4-page LaTeX evaluation paper detailing fragility of metacognitive retrieval signals across quantized API endpoints.
- [ ] **Author Outreach**: Draft email/message to paper authors detailing findings.
