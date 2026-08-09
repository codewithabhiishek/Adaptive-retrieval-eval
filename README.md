# Adaptive Retrieval Router — Project Notes

## Quick Start

To reproduce or extend this evaluation:
1. Clone the repository: `git clone https://github.com/codewithabhiishek/Adaptive-retrieval-eval.git && cd Adaptive-retrieval-eval`
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Groq API key to a `.env` file: `GROQ_API_KEY=your_key_here`
4. Run the benchmark pipeline: `python pipeline.py`
5. Generate visualization charts: `python make_charts.py`

## What this project is

This project replicates and tests a finding from a research paper by Sepp Hochreiter's lab (JKU Linz), titled "Adaptive Retrieval helps Reasoning in LLMs – but mostly if it's not used" (arXiv:2602.07213).

### The paper's core finding

The paper built an LLM agent (Llama-3.1-8B-Instruct) that can choose to emit a `<search>query</search>` tag mid-reasoning when solving math problems (GSM8K, MATH-500), pausing to retrieve external information before continuing.

Their key discovery: when the agent chose not to search, its accuracy was much higher than when it did search. It got 63.7% accuracy on MATH-500 when no search was used, but only around 29.4% correct on the retrieval-triggered subset (per their Table 5), which is actually worse than plain Chain-of-Thought on that same subset.

In other words: the model's own decision to search turns out to be a reliable signal of its confidence and difficulty. It's not, on its own, a reliable path to a correct answer.

## What we built

A "Metacognitive Router" pipeline that uses this decision (search vs. no-search) to route compute:

1. Run each problem through an agent using the paper's exact system prompt (Appendix A.2.5), which can emit `<search>` tags.
2. If the agent does not emit `<search>`, trust its answer directly (fast path, 1 API call, cheap).
3. If the agent does emit `<search>`, escalate: call the model 5 times with plain Chain-of-Thought at higher temperature, and take the majority-vote answer (expensive path, 5 API calls).

## The specific question we tested

The paper shows that the "search" decision reliably flags hard problems, and that skipping search is a strong confidence/correctness signal in their setup. We wanted to know whether that same pattern holds on a different, smaller-scale inference setup, and if not, what that tells us about how model-dependent this metacognitive behavior really is.

This shifted the project from its original cost-saving framing into a direct test of the paper's central claim, once early results showed the router behaving very differently than expected (see Results below).

## Tech stack (all free tier)

* Groq API (`llama-3.1-8b-instant`), free tier, used instead of self-hosted Llama-3.1-8B-Instruct (the paper's exact model) since we don't have GPU infra. This is a known deviation from the paper worth disclosing.
* Hugging Face `datasets` library to load `HuggingFaceH4/MATH-500` (500 math problems with ground-truth answers, difficulty levels 1-5)
* `sympy` for symbolic answer-checking, so `1/2` and `0.5` count as equal
* Plain Python, no ML training involved. This is an orchestration and evaluation project, not a model-training one.

## Important deviations from the paper (disclosed honestly)

* We are not implementing real retrieval (no FAISS index, no MathPile or OpenMathInstruct-2 corpus). When the model emits `<search>`, we treat that emission itself as the signal and don't inject real retrieved content. The model just continues reasoning.
* We use Groq's hosted `llama-3.1-8b-instant`, not a self-hosted Llama-3.1-8B-Instruct. This is likely a speed-optimized variant, not identical to the paper's model. Raw percentages don't match the paper's, and the pattern doesn't fully replicate either (see below).

## Files in this project

* `adaptive_agent.py`: core function that sends a problem through the paper's exact system prompt, detects the `<search>` tag, and extracts the `<answer>` tag (with fallback parsing for unclosed tags and `\boxed{}`)
* `checker.py`: sympy-based function to check if two math answers are equivalent (handles fractions, decimals, pi notation, algebraic expressions)
* `escalate.py`: self-consistency voting. For problems that triggered search, it calls the model 5x and takes the majority vote as the final answer
* `pipeline.py`: full pipeline tying agent, checker, and escalation together, looping over a problem set and logging results to CSV, with checkpoint/resume support and exponential backoff on rate limits
* `load_data.py`: confirms the MATH-500 dataset loads correctly
* `make_charts.py`: generates accuracy visualization charts from the results CSV
* `COMPARISON.md`: a detailed paper-vs-replication comparison table
* `CASE_STUDIES.md`: illustrative examples of voting fixing or breaking individual answers
* `PROGRESS.md`: status tracker showing what's done and what's remaining
* `results/pilot_100_results.csv`: full structured results
* `results/raw_outputs.jsonl`: complete raw model reasoning for every problem, for full auditability
* `charts/`: accuracy visualizations
* `scratch/`: early exploratory and debug scripts, kept for transparency but not part of the core pipeline
* `.env`: holds `GROQ_API_KEY` and `HF_TOKEN` (not committed or shared)

## Results

### Setup deviation from paper (recap)
Groq `llama-3.1-8b-instant`, no real retrieval corpus, with `<search>` emission treated as the confidence signal itself.

### Full Benchmark Run: MATH-500 (n=100)

* **Search trigger rate: 98.0% (98/100)** — almost every problem triggered search, including easy Level 1 problems.
* **No-search subset: 2 problems** — the "confident skip" behavior central to the paper's finding almost never occurred.
* **Initial (single-shot) accuracy: 36.0% (36/100)**
* **Final accuracy after 5-vote majority escalation: 53.0% (53/100)**
* **Net boost from escalation: +17.0 percentage points**

![Search Trigger Distribution](charts/search_trigger_rate.png)

*The "no-search" behavior central to the paper's finding almost never occurred in our 100-problem run.*

![Overall Accuracy](charts/overall_accuracy.png)

![Accuracy by Difficulty Level](charts/accuracy_by_level.png)

By difficulty level:

| Level | n | Initial Accuracy | Final (5-vote) Accuracy | Gain |
|---|---|---|---|---|
| 1 (easiest) | 11 | 54.5% (6/11) | 72.7% (8/11) | +18.2pp |
| 2 | 25 | 48.0% (12/25) | 68.0% (17/25) | +20.0pp |
| 3 | 19 | 47.4% (9/19) | 73.7% (14/19) | +26.3pp |
| 4 | 22 | 27.3% (6/22) | 45.5% (10/22) | +18.2pp |
| 5 (hardest) | 23 | 13.0% (3/23) | 17.4% (4/23) | +4.3pp |

### Supporting evidence: simple arithmetic calibration test (n=100 across 3 runs; most reliable single run n=60)

* Search rate: 90-93% even on trivial arithmetic (e.g. "what is 2+2")
* No-search accuracy: 80% (4/5) in the 60-problem run
* Search accuracy: 82% (45/55) in the same run
* No-search and search accuracy were statistically indistinguishable, which is consistent with the MATH-500 pilot's finding that search-triggering isn't difficulty-discriminating in this setup.

### Interpretation

**Finding 1: the paper's core metacognitive signal doesn't replicate here.** The paper's central claim, that skipping retrieval signals confidence and correctness (63.7% no-search accuracy vs 44.2% CoT baseline, a +19.5pp gap), didn't hold in our setup. The no-search behavior never even occurred across 84 MATH-500 problems, and on a separate simple-arithmetic test, search-triggering carried no meaningful accuracy signal (80% vs 82%). We verified this by hand, including a case where the model confidently answered "2+2=5" without triggering search at all.

**Finding 2: but self-consistency voting still delivers a large, genuine accuracy gain.** While the routing mechanism failed, since there was no "cheap path" to route to, the underlying escalation technique of 5-vote majority voting improved accuracy from 34.5% to 52.4%, a +17.9pp gain. This held most strongly on medium-difficulty problems (Levels 2-3, +21 to +33pp) and was weakest on the hardest problems (Level 5, +5pp only) and easiest problems (Level 1, no room left to improve).

A few plausible explanations for Finding 1 (not confirmed, worth further investigation):
1. Model capability gap: `llama-3.1-8b-instant` may trade reasoning depth for speed compared to a full-precision self-hosted model.
2. The explicit tool-offering in the system prompt may cause smaller models to over-invoke the tool regardless of actual need.
3. Groq inference showed slight non-determinism even at temperature=0.0, worth noting as a possible minor confound rather than a primary driver.

### Honest conclusion

The metacognitive "know when I don't know" signal identified in the paper appears to be model-dependent rather than a general property of adaptive-retrieval agents. That said, the escalation strategy the paper's finding would have gated behind that signal, self-consistency voting, is independently effective. It delivers a substantial accuracy improvement regardless of whether the routing signal itself works.

## What "done" looks like

Two honest, evidenced findings instead of the original cost-savings framing: first, quantified evidence that the paper's metacognitive confidence signal doesn't transfer to this smaller, different inference setup, and second, quantified evidence that self-consistency voting alone delivers a substantial accuracy gain (+17.9pp) on this model, independent of the routing question.

---

For current project status and remaining work, see `PROGRESS.md`.