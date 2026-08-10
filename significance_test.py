import os
import csv
import numpy as np
from statsmodels.stats.contingency_tables import mcnemar

PILOT_CSV = os.path.join("results", "pilot_100_results.csv")
NO_TOOL_CSV = os.path.join("results", "no_tool_baseline_results.csv")
OUTPUT_MD = "SIGNIFICANCE_RESULTS.md"

def parse_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ["true", "1", "yes"]
    return bool(val)

def run_bootstrap_ci(tool_correct, no_tool_correct, n_iterations=2000, seed=42):
    np.random.seed(seed)
    n = len(tool_correct)
    tool_arr = np.array(tool_correct, dtype=int)
    no_tool_arr = np.array(no_tool_correct, dtype=int)
    
    diffs = []
    for _ in range(n_iterations):
        indices = np.random.choice(n, size=n, replace=True)
        tool_sample = tool_arr[indices]
        no_tool_sample = no_tool_arr[indices]
        diff_pp = (no_tool_sample.mean() - tool_sample.mean()) * 100.0
        diffs.append(diff_pp)
        
    lower_ci = np.percentile(diffs, 2.5)
    upper_ci = np.percentile(diffs, 97.5)
    return lower_ci, upper_ci

def run_significance_analysis():
    if not os.path.exists(PILOT_CSV) or not os.path.exists(NO_TOOL_CSV):
        raise FileNotFoundError("Missing required CSV files for significance testing.")

    # Load pilot results (tool-offered)
    pilot_dict = {}
    with open(PILOT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = int(r["problem_id"])
            pilot_dict[pid] = {
                "difficulty": r["difficulty"].replace("Level", "").strip(),
                "initial_correct": parse_bool(r["initial_correct"])
            }

    # Load no-tool baseline results
    no_tool_dict = {}
    with open(NO_TOOL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = int(r["problem_id"])
            no_tool_dict[pid] = {
                "difficulty": r["difficulty"].replace("Level", "").strip(),
                "is_correct": parse_bool(r["is_correct"])
            }

    # Match by problem_id
    matched_ids = sorted(set(pilot_dict.keys()).intersection(set(no_tool_dict.keys())))
    print(f"Matched {len(matched_ids)} problems across both conditions.")

    overall_tool = [pilot_dict[pid]["initial_correct"] for pid in matched_ids]
    overall_no_tool = [no_tool_dict[pid]["is_correct"] for pid in matched_ids]
    overall_levels = [pilot_dict[pid]["difficulty"] for pid in matched_ids]

    # Function to calculate McNemar table and stats
    def evaluate_mcnemar(tool_vec, no_tool_vec):
        # a: both correct, b: tool correct & no-tool incorrect
        # c: tool incorrect & no-tool correct, d: both incorrect
        a = sum(1 for t, nt in zip(tool_vec, no_tool_vec) if t and nt)
        b = sum(1 for t, nt in zip(tool_vec, no_tool_vec) if t and not nt)
        c = sum(1 for t, nt in zip(tool_vec, no_tool_vec) if not t and nt)
        d = sum(1 for t, nt in zip(tool_vec, no_tool_vec) if not t and not nt)

        table = [[a, b], [c, d]]
        
        # Exact binomial test for McNemar (recommended for small/moderate sample sizes)
        res_exact = mcnemar(table, exact=True)
        # Chi-squared asymptotic test with continuity correction
        res_chisq = mcnemar(table, exact=False, correction=True)
        
        p_val = res_exact.pvalue
        stat = res_chisq.statistic
        
        tool_acc = np.mean(tool_vec) * 100.0
        no_tool_acc = np.mean(no_tool_vec) * 100.0
        diff_pp = no_tool_acc - tool_acc
        
        lower_ci, upper_ci = run_bootstrap_ci(tool_vec, no_tool_vec)

        return {
            "n": len(tool_vec),
            "tool_acc": round(tool_acc, 1),
            "no_tool_acc": round(no_tool_acc, 1),
            "diff_pp": round(diff_pp, 1),
            "both_correct": a,
            "tool_only_win": b,
            "no_tool_only_win": c,
            "both_incorrect": d,
            "chi2_stat": round(float(stat), 4),
            "p_value": float(p_val),
            "is_significant": bool(p_val < 0.05),
            "ci_95": (round(float(lower_ci), 1), round(float(upper_ci), 1))
        }

    # 1. Overall analysis
    overall_res = evaluate_mcnemar(overall_tool, overall_no_tool)

    # 2. Per-level analysis
    level_results = {}
    sorted_levels = sorted(set(overall_levels), key=lambda x: int(x) if x.isdigit() else 999)

    for lvl in sorted_levels:
        lvl_indices = [i for i, l in enumerate(overall_levels) if l == lvl]
        lvl_tool = [overall_tool[i] for i in lvl_indices]
        lvl_no_tool = [overall_no_tool[i] for i in lvl_indices]
        level_results[lvl] = evaluate_mcnemar(lvl_tool, lvl_no_tool)

    # Print summary to stdout
    print("\n================ STATISTICAL SIGNIFICANCE TEST RESULTS ================")
    print(f"Overall (n={overall_res['n']}):")
    print(f"  Tool Offered Accuracy: {overall_res['tool_acc']}%")
    print(f"  No-Tool Baseline Accuracy: {overall_res['no_tool_acc']}%")
    print(f"  Accuracy Difference: +{overall_res['diff_pp']}pp")
    print(f"  95% Bootstrap CI: [{overall_res['ci_95'][0]}pp, {overall_res['ci_95'][1]}pp]")
    print(f"  McNemar Chi2 Statistic: {overall_res['chi2_stat']}")
    print(f"  McNemar p-value: {overall_res['p_value']:.4f}")
    print(f"  Statistically Significant (p < 0.05): {overall_res['is_significant']}")
    print("=======================================================================\n")

    # Generate SIGNIFICANCE_RESULTS.md report
    md = f"""# Statistical Significance Testing: No-Tool Baseline vs. Tool-Offered

This document reports McNemar's test for paired binary outcomes and 95% bootstrap confidence intervals comparing single-pass accuracy when the search tool is offered versus when no tool is mentioned across matched MATH-500 problems ($n={overall_res['n']}$).

## 1. Overall Significance Test Summary ($n={overall_res['n']}$)

| Condition / Metric | Tool Offered Initial Pass | No-Tool Baseline (Plain CoT) | Difference (pp) | 95% Bootstrap CI (pp) | McNemar Statistic ($\\\\chi^2$) | p-value | Statistically Significant ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall (n={overall_res['n']})** | {overall_res['tool_acc']}% | {overall_res['no_tool_acc']}% | +{overall_res['diff_pp']}pp | [{overall_res['ci_95'][0]}pp, {overall_res['ci_95'][1]}pp] | {overall_res['chi2_stat']} | {overall_res['p_value']:.4f} | **{'Yes' if overall_res['is_significant'] else 'No'}** |

---

## 2. Difficulty Level Significance & Sample Size Breakdown

| Difficulty Level | Sample Size ($n$) | Tool Offered Accuracy (%) | No-Tool Baseline Accuracy (%) | Difference (pp) | 95% Bootstrap CI (pp) | McNemar Statistic ($\\\\chi^2$) | p-value | Significant ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for lvl in sorted_levels:
        r = level_results[lvl]
        sig_str = "Yes" if r["is_significant"] else "No"
        diff_str = f"+{r['diff_pp']}pp" if r['diff_pp'] > 0 else f"{r['diff_pp']}pp"
        md += f"| **Level {lvl}** | {r['n']} | {r['tool_acc']}% | {r['no_tool_acc']}% | {diff_str} | [{r['ci_95'][0]}pp, {r['ci_95'][1]}pp] | {r['chi2_stat']} | {r['p_value']:.4f} | {sig_str} |\n"

    md += f"""
---

## 3. Per-Level Factual Sample Size Notes

- **Level 1 (n={level_results['1']['n']}):** Sample size is $n={level_results['1']['n']}$; McNemar test $p={level_results['1']['p_value']:.4f}$ (Discordant pairs: No-tool only win = {level_results['1']['no_tool_only_win']}, Tool only win = {level_results['1']['tool_only_win']}).
- **Level 2 (n={level_results['2']['n']}):** Sample size is $n={level_results['2']['n']}$; McNemar test $p={level_results['2']['p_value']:.4f}$ (Discordant pairs: No-tool only win = {level_results['2']['no_tool_only_win']}, Tool only win = {level_results['2']['tool_only_win']}).
- **Level 3 (n={level_results['3']['n']}):** Sample size is $n={level_results['3']['n']}$; McNemar test $p={level_results['3']['p_value']:.4f}$ (Discordant pairs: No-tool only win = {level_results['3']['no_tool_only_win']}, Tool only win = {level_results['3']['tool_only_win']}).
- **Level 4 (n={level_results['4']['n']}):** Sample size is $n={level_results['4']['n']}$; McNemar test $p={level_results['4']['p_value']:.4f}$ (Discordant pairs: No-tool only win = {level_results['4']['no_tool_only_win']}, Tool only win = {level_results['4']['tool_only_win']}).
- **Level 5 (n={level_results['5']['n']}):** Sample size is $n={level_results['5']['n']}$; McNemar test $p={level_results['5']['p_value']:.4f}$ (Discordant pairs: No-tool only win = {level_results['5']['no_tool_only_win']}, Tool only win = {level_results['5']['tool_only_win']}).
"""

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Saved significance test summary to {OUTPUT_MD}")

if __name__ == "__main__":
    run_significance_analysis()
