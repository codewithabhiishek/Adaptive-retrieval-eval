# Follow-Up Experiments Progress & Status Tracking

This file tracks the status of follow-up experiments designed to investigate the high search trigger rate and evaluate tool-use behavior in hosted inference environments.

---

## 1. Experiment Status Overview

| Task / Experiment | Status | Output Artifacts | Notes |
| :--- | :---: | :--- | :--- |
| **Task 1: Stop-at-`</search>` Experiment** | **Done** | `stop_at_search.py`<br>`results/stop_at_search_results.csv`<br>`results/raw_stop_at_search.jsonl` | Evaluated full 100 problems. Search trigger rate remained at **97.0%** (97/100). Resumed accuracy reached **45.0%**. |
| **Task 2: Difficulty-Level Search Trigger Breakdown** | **Done** | `search_rate_by_level.py`<br>`results/search_rate_by_level.csv`<br>`LEVEL_BREAKDOWN.md` | Data extracted from `pilot_100_results.csv` ($n=100$) and exported to CSV and Markdown table. |
| **Task 3: Follow-up Progress Tracking** | **Done** | `FOLLOWUP_PROGRESS.md` | All follow-up tasks completed and tracked. |
| **Task 4: Follow-up Session Changelog** | **Done** | `CHANGELOG_FOLLOWUP.md` | Tracking changes and isolated additions. |

---

## 2. Empirical Results Summary (Task 1: Stop-at-`</search>`)

Evaluating all $n=100$ MATH-500 problems with explicit generation stopping at `</search>` yielded the following key empirical findings:

* **Search Trigger Rate:** **97.0% (97/100)**
  - Halting generation immediately at `</search>` did **not** reduce the search trigger rate compared to continuous single-pass generation (97.0% vs 98.0%).
  - **Conclusion:** The high tool invocation rate is driven primarily by model/endpoint characteristics (e.g. quantization / Groq API tool-use tuning), rather than continuous token generation.

* **Accuracy After Empty-Retrieval Resumption:** **45.0% (45/100)**
  - Resuming step-by-step reasoning after an empty search signal yielded **45.0% single-pass accuracy** (up from 36.0% initial single-pass accuracy in continuous generation).
  - Breakdown by difficulty: Level 1 (72.7%), Level 2 (64.0%), Level 3 (63.2%), Level 4 (27.3%), Level 5 (13.0%).

---

## 3. Documentation Alignment & Sample Size Reconciliation

> [!NOTE]
> **Sample Size Reconciled:**
> - `COMPARISON.md` and `CASE_STUDIES.md` have been updated to reflect the canonical $n=100$ dataset.
> - All documentation files (`README.md`, `COMPARISON.md`, `CASE_STUDIES.md`, `LEVEL_BREAKDOWN.md`, `NO_TOOL_COMPARISON.md`, `SIGNIFICANCE_RESULTS.md`) are now 100% aligned on the canonical $n=100$ MATH-500 test dataset.
