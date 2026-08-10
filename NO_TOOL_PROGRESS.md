# No-Tool Baseline Experiment Progress & Status Tracking

This document tracks the status, progress, rate-limit events, and completion count for the No-Tool Baseline experiment on MATH-500.

---

## 1. Experiment Status Overview

| Metric / Aspect | Value / Status |
| :--- | :--- |
| **Experiment Status** | **Done** |
| **Target Dataset** | MATH-500 ($n=100$) |
| **System Prompt Style** | Plain Chain-of-Thought (No `<search>` tool mentioned) |
| **Completed Count** | 100 / 100 |
| **Output CSV** | `results/no_tool_baseline_results.csv` |
| **Raw Output Log** | `results/raw_no_tool_baseline.jsonl` |
| **Comparison Markdown** | `NO_TOOL_COMPARISON.md` |

---

## 2. Execution Log & Results Summary

- [x] Created `no_tool_baseline.py` with standalone CoT system prompt (no tool references).
- [x] Configured checkpointing and auto-resume.
- [x] Executed 5-problem test run (80% accuracy).
- [x] Executed full 100-problem run (100% completion).
- [x] Generated `NO_TOOL_COMPARISON.md` comparison table.

### Summary Metrics ($n=100$)
- **Tool-Offered Initial Single-Pass Accuracy:** 36.0% (36/100)
- **No-Tool Baseline (Plain CoT) Accuracy:** 48.0% (48/100)
- **Net Accuracy Difference:** **+12.0 percentage points** (No-Tool higher)
