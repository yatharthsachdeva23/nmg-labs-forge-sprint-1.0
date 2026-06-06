# DECISIONS.md — decision & learnings log

A short running note of the real choices you made: what you tried, what failed and why, what
you changed. This is your engineering judgement on the record — it is what separates a builder
from a button-presser, and it is graded (challenge brief section 08).

Append a 1–2 line entry whenever you make a real decision or hit/fix a wall. Add a timestamp.

Format:
`[HH:MM] <decision or problem> → <what you did and why>`

---

## Example (replace with your own)

- `[10:20]` Chose plain-csv parsing over pandas → fewer deps, fast enough for 5k rows, model
  quota saved for the fixer.
- `[11:05]` Title detector over-counted duplicates → realized non-indexable pages were
  included; added an indexable+200 filter (per rulebook).
- `[12:40]` Dashboard wasn't updating live → MCP tool wasn't emitting the SSE event; added
  `_emit("issue", row)` in extract.

---

## My log

- [12:05] Initializing the 6-hour sprint. Decided to build a strict deterministic split-engine inside seo/detector.py to handle rules without overflowing local model memory.
- [12:12] Encountered initial path FileNotFoundError. Resolved by correcting the export directory path relative to execution root. Confirmed successful baseline completion. Moving to integrate single-row issue rules.
- [12:28] Implemented 7 single-row deterministic evaluation rules (short titles, meta description limits, missing H1s, thin content, and response speed thresholds) to ensure high-fidelity checking.
- [12:39] Successfully integrated duplicate content logic matrices and multi-hop redirect graph detectors. Verified the headless runner loop completes smoothly with zero compilation overhead.
- [12:58] Switched architecture to Track A Ollama Cloud. Selected gemma4:31b-cloud as primary driver. Implemented a strict batched fixing pipeline to conserve cloud compute time quota.
- [13:05] Successfully integrated the automated run_cloud_fixer engine inside server.py. Verified that title length guards and path-similarity redirect maps write seamlessly to output schemas without expanding cloud compute time overhead.
