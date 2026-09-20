---
applyTo: "evaluate_embeddings.py,encode_with_finbert.py,evaluate_downstream_probe.py"
---

# Testing / Evaluation Instructions

When working on embedding generation or evaluation code in this repo, consult
[docs/testing.md](../../docs/testing.md) for the full evaluation methodology before
making changes.

- `encode_with_finbert.py` produces the embeddings; `evaluate_embeddings.py` computes
  proxy quality metrics (isotropy, pairwise similarity, cluster purity, ticker
  retrieval P@k/MRR) against a SQLite DB produced by the encoder. See
  [docs/testing.md](../../docs/testing.md) for what each metric means and how to run it.
- These proxy metrics only sanity-check that embeddings are non-degenerate and
  topically meaningful — they are not evidence of downstream price-prediction quality.
  Do not present proxy metric improvements as proof embeddings improve trading model
  accuracy.
- The actual quality bar for this project is the downstream probe described in
  [docs/testing.md](../../docs/testing.md#planned-downstream-probe-evaluate_downstream_probepy)
  (`evaluate_downstream_probe.py`, not yet implemented — pending historical candle
  data). When candle data becomes available and this script is implemented, follow the
  design already documented there (target construction, time-based train/test split,
  baseline comparisons, final ablation) rather than inventing a new approach.
