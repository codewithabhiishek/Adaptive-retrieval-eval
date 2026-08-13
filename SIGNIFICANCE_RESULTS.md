# Statistical Significance Testing: No-Tool Baseline vs. Tool-Offered

This document reports McNemar's test for paired binary outcomes and 95% bootstrap confidence intervals comparing single-pass accuracy when the search tool is offered versus when no tool is mentioned across matched MATH-500 problems ($n=100$).

## 1. Overall Significance Test Summary ($n=100$)

| Condition / Metric | Tool Offered Initial Pass | No-Tool Baseline (Plain CoT) | Difference (pp) | 95% Bootstrap CI (pp) | McNemar Statistic ($\\chi^2$) | p-value | Statistically Significant ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall (n=100)** | 36.0% | 48.0% | +12.0pp | [4.0pp, 20.0pp] | 6.05 | 0.0118 | **Yes** |

---

## 2. Difficulty Level Significance & Sample Size Breakdown

| Difficulty Level | Sample Size ($n$) | Tool Offered Accuracy (%) | No-Tool Baseline Accuracy (%) | Difference (pp) | 95% Bootstrap CI (pp) | McNemar Statistic ($\\chi^2$) | p-value | Significant ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Level 1** | 11 | 54.5% | 63.6% | +9.1pp | [-18.2pp, 36.4pp] | 0.0 | 1.0000 | No |
| **Level 2** | 25 | 48.0% | 64.0% | +16.0pp | [4.0pp, 32.0pp] | 2.25 | 0.1250 | No |
| **Level 3** | 19 | 47.4% | 68.4% | +21.1pp | [0.0pp, 42.1pp] | 1.5 | 0.2188 | No |
| **Level 4** | 22 | 27.3% | 40.9% | +13.6pp | [0.0pp, 27.3pp] | 1.3333 | 0.2500 | No |
| **Level 5** | 23 | 13.0% | 13.0% | 0.0pp | [-17.4pp, 17.4pp] | 0.25 | 1.0000 | No |

---

## 3. Per-Level Factual Sample Size Notes

- **Level 1 (n=11):** Sample size is $n=11$; McNemar test $p=1.0000$ (Discordant pairs: No-tool only win = 2, Tool only win = 1).
- **Level 2 (n=25):** Sample size is $n=25$; McNemar test $p=0.1250$ (Discordant pairs: No-tool only win = 4, Tool only win = 0).
- **Level 3 (n=19):** Sample size is $n=19$; McNemar test $p=0.2188$ (Discordant pairs: No-tool only win = 5, Tool only win = 1).
- **Level 4 (n=22):** Sample size is $n=22$; McNemar test $p=0.2500$ (Discordant pairs: No-tool only win = 3, Tool only win = 0).
- **Level 5 (n=23):** Sample size is $n=23$; McNemar test $p=1.0000$ (Discordant pairs: No-tool only win = 2, Tool only win = 2).
