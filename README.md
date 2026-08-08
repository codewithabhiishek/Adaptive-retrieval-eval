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

* `test_api.py` — confirms Groq API key works
* `load_data.py` — confirms MATH-500 dataset loads correctly
* `adaptive_agent.py` — core function: sends a problem through the
  paper's exact system prompt, detects `<search>` tag, extracts
  `<answer>` tag (with fallback parsing for unclosed tags and `\boxed{}`)
* `checker.py` — sympy-based function to check if two math answers are
  equivalent (handles fractions, decimals, pi notation, algebraic
  expressions)
* `escalate.py` — self-consistency voting: for problems that triggered
  search, call the model 5x and take majority vote as final answer
* `pipeline.py` — full pipeline tying agent + checker + escalation
  together, loops over a problem set, logs results to CSV
* `test_calibration_large.py` — generates simple arithmetic problems to
  test whether search-rate tracks difficulty independent of MATH-500's
  complexity/LaTeX-heavy phrasing
* `.env` — holds `GROQ_API_KEY` and `HF_TOKEN` (not committed/shared)

## Actual Results

### Setup deviation from paper (recap)
Groq `llama-3.1-8b-instant`, no real retrieval corpus, `<search>`
emission treated as the confidence signal itself.

### Finding 1: MATH-500 smoke test (n=15)
* Search rate: 100% (15/15) — every problem triggered search, including
  Level 1-2 easy problems.
* Overall accuracy: 40% (6/15)
* Could not evaluate no-search accuracy (zero no-search cases occurred)

### Finding 2: Simple arithmetic calibration test (n=100 across 3 runs;
most reliable single run n=60)
* Search rate: 90-93% even on trivial arithmetic (e.g. "what is 2+2")
* No-search accuracy: 80% (4/5) in the 60-problem run
* Search accuracy: 82% (45/55) in the same run
* **Key result: no-search and search accuracy are statistically
  indistinguishable in this setup (80% vs 82%).**

### Interpretation
The paper's central finding — that the model's decision to skip
retrieval is a reliable signal of confidence and correctness (in their
data: 63.7% no-search accuracy vs 44.2% CoT baseline on MATH-500, a
+19.5pp gap) — does NOT replicate with this model/inference setup. In
our data, whether the model searches or not carries almost no
information about whether its answer will be correct.

This is a genuine, honest divergence, not a bug — verified by manually
reviewing raw model outputs (e.g. the model confidently answered
"2 + 2 = 5" without triggering search, while correctly answering
"what is the square root of 9" only after triggering search).

Plausible explanations (not confirmed, worth further investigation):
1. Model capability gap — `llama-3.1-8b-instant` may trade reasoning
   depth for speed compared to a full-precision self-hosted model.
2. The explicit tool-offering in the system prompt may cause smaller
   models to over-invoke the tool regardless of actual need, rather
   than reflecting genuine uncertainty.
3. Groq inference showed slight non-determinism even at temperature=0.0
   (same problem set, same seed, produced different wrong answers on a
   repeat run) — worth noting as a possible minor confound.

### Honest conclusion
The metacognitive "know when I don't know" signal identified in the
paper appears to be model-dependent rather than a general property of
adaptive-retrieval agents. Smaller or differently-tuned models may not
exhibit reliable self-calibration even when given the same prompting
structure.

## Status / progress log

* [x] Environment set up (venv, libraries installed)
* [x] Groq API key + HF token confirmed working
* [x] MATH-500 dataset loads correctly (500 problems confirmed)
* [x] Adaptive agent call function built, tested, hardened against
      unclosed tags and `\boxed{}` fallback answers
* [x] Answer-equivalence checker built and tested (fractions, decimals,
      algebraic expressions, tuples with pi) — all passing
* [x] Escalation (self-consistency voting) function built and tested
* [x] Full pipeline script built, run on MATH-500 smoke test (n=15)
* [x] Follow-up calibration tests built and run (n=10, 30, 60) on
      simple arithmetic to isolate difficulty-independence of search
      behavior
* [x] Manually spot-checked outputs by hand (confirmed genuine model
      behavior, not a parsing bug)
* [x] Results summarized above

## What "done" looks like (achieved)

Not the original cost-savings framing, but a clearer, better-evidenced
result: quantified evidence that the paper's core metacognitive
confidence signal does not transfer reliably to a smaller/different
inference setup, with a specific, reproducible example (2+2=5,
no-search) supporting it.