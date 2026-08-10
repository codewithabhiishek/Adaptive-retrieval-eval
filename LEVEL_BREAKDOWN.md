# MATH-500 Search Trigger Rate & Accuracy by Difficulty Level

This document provides a breakdown of search trigger behavior and accuracy metrics across MATH-500 difficulty levels (Level 1 to 5) based on the full $n=100$ evaluation dataset (`results/pilot_100_results.csv`).

## Search Trigger Rate & Performance Breakdown Table

| Difficulty Level | Sample Size ($n$) | Search Triggered | Search Trigger Rate (%) | Initial Accuracy (%) | Final Accuracy (5-Vote %) | Net Boost (pp) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Level 1** | 11 | 11 / 11 | 100.0% | 54.5% | 72.7% | +18.2pp |
| **Level 2** | 25 | 25 / 25 | 100.0% | 48.0% | 68.0% | +20.0pp |
| **Level 3** | 19 | 17 / 19 | 89.5% | 47.4% | 73.7% | +26.3pp |
| **Level 4** | 22 | 22 / 22 | 100.0% | 27.3% | 45.5% | +18.2pp |
| **Level 5** | 23 | 23 / 23 | 100.0% | 13.0% | 17.4% | +4.3pp |
| **Overall (Total)** | **100** | **98 / 100** | **98.0%** | **36.0%** | **53.0%** | **+17.0pp** |

## Key Observations

1. **Uniformly High Search Triggering Across All Difficulty Levels:**
   - Even on **Level 1 (Easiest)** problems, the model triggered search on 11 out of 11 problems (**100.0%**).
   - Search trigger rates remain near ~90%–100% across all levels (Level 1: 100.0%, Level 2: 100.0%, Level 3: 89.5%, Level 4: 100.0%, Level 5: 100.0%).
   - This empirically demonstrates that on this hosted API environment (`llama-3.1-8b-instant`), tool-use triggering does not vary with difficulty, preventing any difficulty-based selective retrieval routing.

2. **Escalation (5-Vote Majority) Effectiveness:**
   - Voting provides massive performance gains on medium-difficulty problems: Level 2 (+20.0pp), Level 3 (+26.3pp), Level 4 (+18.2pp).
   - On extreme difficulty (Level 5), voting provides a modest gain (+4.3pp), as many Level 5 problems remain beyond single-pass CoT capabilities.
