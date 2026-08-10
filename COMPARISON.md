# Comparative Study: Paper Findings vs. Our API Evaluation

This document presents a side-by-side comparative analysis of the
original research paper by Hochreiter et al. (arXiv:2602.07213) and our
independent, small-scale replication attempt using hosted API inference.

---

## 1. Overview & Core Setup

| Aspect | Original Paper (Hochreiter et al.) | Our Replication Attempt |
| :--- | :--- | :--- |
| **Paper Title** | *Adaptive Retrieval helps Reasoning in LLMs – but mostly if it's not used* | N/A (this is an independent evaluation, not a published paper) |
| **Model Used** | `Llama-3.1-8B-Instruct` (self-hosted, FP16) | `llama-3.1-8b-instant` (Groq-hosted API; exact quantization/optimization not publicly confirmed, but Groq's "instant" variants are generally speed-optimized) |
| **Inference Hardware** | Local GPU infrastructure | Groq Cloud LPU hardware (hosted, not self-managed) |
| **Primary Goal** | Show that the model's search decision acts as a reliable confidence signal | Test whether the same pattern holds on a different, freely-accessible inference setup |

---

## 2. Key Metric Comparison Table (MATH-500)

| Metric / Behavior | Original Paper (MATH-500) | Our Evaluation (n=100) | Notes |
| :--- | :--- | :--- | :--- |
| **Search Trigger Rate** | 38.8% | 98.0% (98/100) | Large divergence — 98% of problems triggered search in our run |
| **No-Search Accuracy** | 63.7% | 50.0% (1/2) | Rare edge case in our run (only 2 no-search cases occurred: 1 correct, 1 incorrect) |
| **CoT-Only Baseline Accuracy** | 44.2% (plain CoT, no search tool offered) | 48.0% (48/100) | Measured in our separate No-Tool baseline experiment (plain CoT) |
| **Our Router's Initial-Pass Accuracy** | N/A | 36.0% (36/100) | First-attempt accuracy with search tool offered before escalation |
| **Escalated / Search-Subset Accuracy** | 29.4% (search-triggered subset, single pass) | 53.0% (53/100) after 5-vote majority escalation | Not directly comparable — paper's number is single-pass; ours is post-voting |
| **Accuracy Gap (no-search vs search)** | +19.5pp (no-search notably higher) | +14.0pp (50% vs 36%, n=2 edge case) | Small sample size (n=2 no-search cases), gap is consistent with chance |

**Important note on comparability:** several paper numbers and our numbers
are not strictly apples-to-apples, since our main pipeline offers the
search tool and our "final" accuracy includes 5-vote self-consistency
escalation, which the paper's single-pass search-subset number does not.
Differences are directional evidence, not a precise like-for-like replication.

---

## 3. Accuracy Breakdown by Difficulty Level (Our Evaluation, n=100)

| Level | Sample Size (n) | Initial Pass Accuracy | Final 5-Vote Accuracy | Net Gain |
| :--- | :--- | :--- | :--- | :--- |
| **Level 1 (Easiest)** | 11 | 54.5% (6/11) | 72.7% (8/11) | +18.2pp |
| **Level 2** | 25 | 48.0% (12/25) | 68.0% (17/25) | +20.0pp |
| **Level 3** | 19 | 47.4% (9/19) | 73.7% (14/19) | +26.3pp |
| **Level 4** | 22 | 27.3% (6/22) | 45.5% (10/22) | +18.2pp |
| **Level 5 (Hardest)** | 23 | 13.0% (3/23) | 17.4% (4/23) | +4.3pp |

*(The paper does not report a directly comparable per-level breakdown
for the search-decision behavior, so this table reflects our own data
only.)*

---

## 4. Possible Explanations for the Divergence (Not Confirmed)

### A. Model differences
* **Self-hosted FP16 (paper)**: full-precision weights, run on local
  GPU infrastructure the authors controlled directly.
* **Groq-hosted `llama-3.1-8b-instant` (ours)**: a speed-optimized
  hosted variant. We cannot confirm the exact quantization or
  optimization Groq applies — this is a plausible contributing factor,
  not a verified one.

### B. Prompt sensitivity
Smaller or differently-tuned models may be more prone to over-invoking
an offered tool regardless of genuine need, rather than reflecting
calibrated uncertainty — this is a hypothesis based on our results, not
something we tested directly against a control condition.

### C. Inference non-determinism
We observed slight non-determinism even at `temperature=0.0` on Groq
(same problem, same seed, different wrong answers on a repeat run) —
worth noting as a minor possible confound, not a primary driver of the
difference.

---

## 5. Hardware Requirements to Replicate the Paper's Exact Self-Hosted Setup

| Resource | Minimum for Self-Hosted FP16 | Our Actual Setup |
| :--- | :--- | :--- |
| **GPU VRAM** | ~24 GB (e.g. RTX 3090/4090, A10G) | None (Groq-hosted) |
| **System RAM** | 32–64 GB | Standard local RAM |
| **Disk Storage** | ~20–50 GB for model weights | ~10 MB (scripts + results only) |
| **Estimated Cloud Cost (if renting)** | ~$0.40–$0.69/hour (RunPod/Vast.ai, approximate) | $0.00 (Groq free tier) |

---

## 6. Conclusion

1. **What this shows**: the paper's core metacognitive finding —
   that skipping retrieval reliably signals confidence and correctness
   — did not replicate on a different, freely-accessible inference
   setup. This suggests the behavior may be sensitive to the specific
   model/inference stack rather than a general property of
   adaptive-retrieval prompting.
2. **What this doesn't show**: we cannot confirm *why* the divergence
   occurs (quantization, prompt sensitivity, or something else) without
   further controlled testing — this remains an open question.
3. **A separate, independently useful finding**: regardless of the
   routing question, 5-vote self-consistency escalation produced a
   real, substantial accuracy improvement (+17.9pp) on this model,
   which stands on its own as a practical result.