# Project Progress Tracker

This file tracks what's done and what's remaining. Read this first if
picking up the project after a break, since it reflects the current
state more precisely than README.md, which only covers the finished
project narrative.

## Current Status: Pilot run 86/100 complete, finalizing results

## Done

- [x] Environment set up (venv, libraries installed)
- [x] Groq API key + HF token confirmed working
- [x] MATH-500 dataset loads correctly (500 problems confirmed)
- [x] `adaptive_agent.py` built and hardened (handles unclosed tags,
      `\boxed{}` fallback, rate-limit backoff/retry)
- [x] `checker.py` built and tested (fractions, decimals, pi notation,
      algebraic expressions, 5/5 manual test cases passing)
- [x] `escalate.py` (5-vote self-consistency voting) built and tested
- [x] `pipeline.py` built with checkpoint/resume support, exponential
      backoff on rate limits, structured CSV + raw JSONL logging
- [x] MATH-500 pilot run: 86/100 problems completed successfully
      (2 problems failed on API rate limits, problem IDs 79 and 81,
      resume logic will retry these automatically)
- [x] Supporting calibration tests run on simple arithmetic (n=10, 30,
      60), confirming search-rate independence from difficulty holds
      outside MATH-500 too
- [x] Manually spot-checked outputs by hand, confirming genuine model
      behavior (e.g. "2+2=5" with no search triggered), not a parsing
      bug
- [x] `COMPARISON.md` written: paper vs. replication comparison, with
      honest caveats on non-comparable metrics and unverified claims
      removed
- [x] `CASE_STUDIES.md` written: illustrative fixed/broken voting
      examples
- [x] Three charts generated and embedded in README:
      `charts/search_trigger_rate.png`, `charts/overall_accuracy.png`,
      `charts/accuracy_by_level.png`
- [x] Repository cleaned: debug/exploratory scripts moved to
      `scratch/`, `.env` confirmed never committed, `.gitignore`
      verified
- [x] README rewritten in clean paragraph style, tracking content
      moved out into this file
- [x] Repository pushed to GitHub

## Remaining

- [ ] Resume pipeline to complete problems 87-100 plus retry the 2
      failed ones (79, 81). Command:
      `./venv/bin/python -c "from pipeline import run_pipeline; run_pipeline(limit=100)"`
- [ ] Recompute final stats once n=100 is complete (overall accuracy,
      per-level breakdown, search rate)
- [ ] Regenerate all three charts (`make_charts.py`) with final n=100
      numbers
- [ ] Update README.md numbers from n=86 interim to final n=100
- [ ] Update COMPARISON.md numbers from n=86 interim to final n=100
- [ ] Final commit and push with the complete dataset

## Known limitations to keep in mind (don't overclaim these away)

- We do not know Groq's exact quantization or optimization for
  `llama-3.1-8b-instant`. Do not state this as fact anywhere.
- Several paper vs. our-results comparisons are not strictly
  apples-to-apples, since they compare different baselines. See
  COMPARISON.md section 2 for the honest breakdown.
- `checker.py` has a few known false-negative cases on formatting
  differences (e.g. `√` vs `\sqrt{}`, unit suffixes like "12 cm" vs
  "12"). A small number of "incorrect" results in the data may
  actually be correct answers with formatting mismatches. Not
  corrected for in the current results, worth mentioning if asked.

## Daily API budget note

Groq's free tier for `llama-3.1-8b-instant` allows 500K tokens/day and
6K tokens/minute, resetting at midnight UTC. A full 100-problem run
with a 90%+ escalation rate uses close to the full daily budget, so
avoid running additional large batches on the same day without
checking usage first at
console.groq.com/settings/organization/usage.