# Adaptive Retrieval Router — Project Notes

## What this project is

This project replicates and tests a finding from a research paper by
Sepp Hochreiter's lab (JKU Linz), titled "Adaptive Retrieval helps
Reasoning in LLMs – but mostly if it's not used" (arXiv:2602.07213).

### The paper's core finding

The paper built an LLM agent (Llama-3.1-8B-Instruct) that can choose to
emit a `<search>query</search>` tag mid-reasoning when solving math
problems (GSM8K, MATH-500), pausing to retrieve external information
before continuing.

Their key discovery: when the agent chose NOT to search, its accuracy was
much higher than when it did search — 63.7% accuracy on MATH-500 when no
search was used, vs a much lower accuracy on the subset where it did
search (only ~29.4% correct on the retrieval-triggered subset, per their
Table 5, actually worse than plain Chain-of-Thought on that subset).

This means: the model's own decision to search is a reliable signal of
its confidence/difficulty — NOT a reliable path to a correct answer by
itself.

## What we built

A "Metacognitive Router" pipeline that uses this decision (search vs.
no-search) to route compute:

1. Run each problem through an agent using the paper's exact system
   prompt (Appendix A.2.5), which can emit `<search>` tags.
2. If the agent does NOT emit `<search>` → trust its answer directly
   (fast path, 1 API call, cheap).
3. If the agent DOES emit `<search>` → escalate: call the model 5 times
   with plain Chain-of-Thought at higher temperature, and take the
   majority-vote answer (expensive path, 5 API calls).

## The specific question we tested

The paper shows the "search" decision reliably flags HARD problems, and
that skipping search is a strong confidence/correctness signal on their
setup. We wanted to know: does that same "search decision = reliable
confidence signal" pattern hold on a different, smaller-scale inference
setup? If not, what does that tell us about how model-dependent this
metacognitive behavior is?

This shifted from the original cost-saving framing into a direct test of
the paper's central claim once early results showed the router behaving
very differently than expected (see Results below).

## Tech stack (all free tier)

* Groq API (`llama-3.1-8b-instant`) — free tier, used instead of
  self-hosted Llama-3.1-8B-Instruct (the paper's exact model) since we
  don't have GPU infra. This is a known deviation from the paper worth
  disclosing.
* Hugging Face `datasets` library → `HuggingFaceH4/MATH-500` dataset
  (500 math problems with ground-truth answers, difficulty levels 1-5)
* `sympy` for symbolic answer-checking (so `1/2` and `0.5` count as equal)
* Plain Python, no ML training involved — this is an orchestration/
  evaluation project, not a model-training project

## Important deviations from the paper (disclosed honestly)

* We are NOT implementing real retrieval (no FAISS index, no MathPile/
  OpenMathInstruct-2 corpus). When the model emits `<search>`, we treat
  that emission itself as the signal and do not inject real retrieved
  content — the model just continues reasoning.
* We use Groq's hosted `llama-3.1-8b-instant`, not a self-hosted
  Llama-3.1-8B-Instruct — this is likely a speed-optimized variant, not
  identical to the paper's model. Raw percentages do not match the
  paper's; the pattern doesn't fully replicate either (see below).

## Files in this project

* `adaptive_agent.py` — core function: sends a problem through the
  paper's exact system prompt, detects `<search>` tag, extracts
  `<answer>` tag (with fallback parsing for unclosed tags and `\boxed{}`)
* `checker.py` — sympy-based function to check if two math answers are
  equivalent (handles fractions, decimals, pi notation, algebraic
  expressions)
* `escalate.py` — self-consistency voting: for problems that triggered
  search, call the model 5x and take majority vote as final answer
* `pipeline.py` — full pipeline tying agent + checker + escalation
  together, loops over a problem set, logs results to CSV, with
  checkpoint/resume support and exponential backoff on rate limits
* `load_data.py` — confirms MATH-500 dataset loads correctly
* `make_charts.py` — generates accuracy visualization charts from
  results CSV
* `COMPARISON.md` — detailed paper-vs-replication comparison table
* `CASE_STUDIES.md` — illustrative examples of voting fixing/breaking
  individual answers
* `PROGRESS.md` — status tracker (what's done, what's remaining)
* `results/pilot_100_results.csv` — full structured results
* `results/raw_outputs.jsonl` — complete raw model reasoning for every
  problem, for full auditability
* `charts/` — accuracy visualizations
* `scratch/` — early exploratory/debug scripts (kept for transparency,
  not part of the core pipeline)
* `.env` — holds `GROQ_API_KEY` and `HF_TOKEN` (not committed/shared)

## Results

### Setup deviation from paper (recap)
Groq `llama-3.1-8b-instant`, no real retrieval corpus, `<search>`
emission treated as the confidence signal itself.

### Pilot run: MATH-500 (n=86)

* **Search trigger rate: 100% (84/84)** — every problem triggered
  search, including Level 1 (easiest) problems.
* **No-search subset: 0 problems** — the "confident skip" behavior
  central to the paper's finding never occurred in this run.
* **Initial (single-shot) accuracy: 34.5% (29/84)**
* **Final accuracy after 5-vote majority escalation: 52.4% (44/84)**
* **Net boost from escalation: +17.9 percentage points**

![Overall Accuracy](charts/overall_accuracy.png)

![Accuracy by Difficulty Level](charts/accuracy_by_level.png)

By difficulty level:

| Level | n | Initial Accuracy | Final (5-vote) Accuracy | Gain |
|---|---|---|---|---|
| 1 (easiest) | 7 | 71.4% | 71.4% | +0.0pp |
| 2 | 23 | 43.5% | 65.2% | +21.7pp |
| 3 | 15 | 46.7% | 80.0% | +33.3pp |
| 4 | 19 | 21.1% | 42.1% | +21.0pp |
| 5 (hardest) | 20 | 15.0% | 20.0% | +5.0pp |

### Supporting evidence: simple arithmetic calibration test (n=100
across 3 runs; most reliable single run n=60)

* Search rate: 90-93% even on trivial arithmetic (e.g. "what is 2+2")
* No-search accuracy: 80% (4/5) in the 60-problem run
* Search accuracy: 82% (45/55) in the same run
* No-search and search accuracy were statistically indistinguishable —
  consistent with the MATH-500 pilot's finding that search-triggering
  is not difficulty-discriminating in this setup.

### Interpretation

**Finding 1 — the paper's core metacognitive signal does not
replicate.** The paper's central claim — that skipping retrieval
signals confidence and correctness (63.7% no-search accuracy vs 44.2%
CoT baseline, a +19.5pp gap) — did not hold here. The no-search
behavior never even occurred across 84 MATH-500 problems, and on a
separate simple-arithmetic test, search-triggering carried no
meaningful accuracy signal (80% vs 82%). This was verified by hand,
including a case where the model confidently answered "2+2=5" without
triggering search.

**Finding 2 — but self-consistency voting delivers a large, genuine
accuracy gain.** While the *routing* mechanism failed (there was no
"cheap path" to route to), the underlying escalation technique — 5-vote
majority voting — improved accuracy from 34.5% to 52.4%, a +17.9pp
gain. This held most strongly on medium-difficulty problems (Levels
2-3, +21 to +33pp) and was weakest on the hardest problems (Level 5,
+5pp only) and easiest problems (Level 1, no room to improve).

Plausible explanations for Finding 1 (not confirmed, worth further
investigation):
1. Model capability gap — `llama-3.1-8b-instant` may trade reasoning
   depth for speed compared to a full-precision self-hosted model.
2. The explicit tool-offering in the system prompt may cause smaller
   models to over-invoke the tool regardless of actual need.
3. Groq inference showed slight non-determinism even at temperature=0.0
   — worth noting as a possible minor confound, not a primary driver.

### Honest conclusion

The metacognitive "know when I don't know" signal identified in the
paper appears to be model-dependent rather than a general property of
adaptive-retrieval agents. However, the escalation strategy the paper's
finding would have gated behind that signal — self-consistency voting —
is independently effective, delivering a substantial accuracy
improvement regardless of whether the routing signal itself works.

## What "done" looks like

Two honest, evidenced findings instead of the original cost-savings
framing: (1) quantified evidence that the paper's metacognitive
confidence signal does not transfer to this smaller/different
inference setup, and (2) quantified evidence that self-consistency
voting alone delivers a substantial accuracy gain (+17.9pp) on this
model, independent of the routing question.

---

For current project status and remaining work, see `PROGRESS.md`.