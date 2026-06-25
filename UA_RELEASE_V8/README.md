# UA Test v8 — Dual-Axis Alignment Evaluation

Standardized evaluation of LLM behavior under irresolvable directive conflict,
measuring two independent axes:

1. **Refusal** — does the agent decline harmful / manipulative instructions?
2. **Moral reasoning** — when every option causes harm, which does it choose,
   and is that choice stable across conditions?

## What v8 adds over earlier protocols

- **Counterbalanced option ordering** — each dilemma runs in both A-B and B-A
  order, yielding a per-model position-bias coefficient.
- **LLM-as-judge refusal second pass** — reclassifies keyword-missed refusals.
- **Thinking-model second pass** — restates the conclusion when no FINAL ANSWER
  is found.
- **Configurable tiers** — Screening (3 MC), Standard (10 MC), Certification (30 MC).
- **Per-model Behavioral Passport** (JSON) with the dual-axis profile.

## Structure

- 14 operational domains × (2 refusal + 2 dilemma) scenarios
- 11 temperatures (0.0–1.0)
- Monte Carlo runs per the chosen tier

## Layout

```
src/ua_v8_full.py                  # the test
results/ua_v8_screening_results.csv  # Screening-tier pilot run (3 MC)
results/ua_v8_screening.log
```

## Run

```bash
python3 src/ua_v8_full.py                     # Standard tier (10 MC)
python3 src/ua_v8_full.py --tier screening    # quick (3 MC)
python3 src/ua_v8_full.py --tier certification # full (30 MC)
```

Requires an OpenAI-compatible endpoint (default: LM Studio at `localhost:1234`).

## Status of included results

`results/` contains a **Screening-tier pilot** (3 MC runs, cell CI ≈ ±12 pp).
Treat it as a smoke/pilot result, not certification-grade. Standard and
Certification runs produce tighter estimates.
