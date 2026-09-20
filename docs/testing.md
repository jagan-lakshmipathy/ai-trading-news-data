# Evaluating Embedding Quality

`evaluate_embeddings.py` computes proxy quality metrics for embeddings produced by
`encode_with_finbert.py`. These metrics sanity-check that embeddings are non-degenerate
and topically meaningful — they do **not** prove the embeddings are predictive for a
downstream price prediction task.

## Usage

```bash
python evaluate_embeddings.py --db your_embeddings.db
```

Optional flags:
- `--n-clusters` (default 20): number of KMeans clusters for the purity check
- `--top-k` (default 10): top-k for retrieval precision/MRR
- `--n-queries` (default 100): number of sampled retrieval queries

## Metrics Reported

### 1. Isotropy (PCA explained variance)
Checks embeddings aren't collapsing into a low-dimensional subspace. A very sharp
concentration of variance in the top component(s) signals dimension collapse /
anisotropy — common in raw BERT `[CLS]` embeddings vs. sentence-transformer embeddings.

### 2. Pairwise cosine similarity
Mean/std cosine similarity across a random sample of embeddings. A mean near 1.0
indicates embeddings are nearly identical (collapsed) and not discriminative.

### 3. Cluster purity vs. channels
Clusters embeddings with KMeans and scores alignment against the `channels` metadata
column using normalized mutual information (NMI). Good embeddings should group
same-channel articles together more than chance.

### 4. Ticker-based retrieval (Precision@k / MRR)
Weak-label retrieval evaluation: for a sample of query articles with known tickers,
checks what fraction of the top-k nearest neighbors share at least one ticker
(Precision@k), and the reciprocal rank of the first ticker-matching result (MRR).

## Why These Are Proxy Metrics, Not Ground Truth

These intrinsic/proxy metrics are useful for catching broken or degenerate embeddings
before spending GPU time training a downstream model, but they are weak evidence for
task-specific quality:

- **Clustering by channel** shows embeddings encode topical/entity information, but
  topical clustering has no necessary relationship to price-relevant signal (sentiment,
  surprise, magnitude of news impact). An embedding could cluster perfectly by channel
  and still be useless for predicting returns.
- **Retrieval P@k/MRR** shows semantically similar articles are near each other — again
  a proxy for "topic," not "market-moving content." Two articles can be topically
  similar but have opposite price implications (e.g., earnings beat vs. miss).
- **Isotropy/pairwise similarity** only confirms the embedding space isn't degenerate —
  necessary but far from sufficient.

## What Actually Justifies Quality for Price Prediction

The only evaluation directly justified for a price prediction use case is a
**downstream probe tied to price outcomes**:

- Train a simple linear/logistic regression (or small MLP) using only the embedding
  (no price candles) to predict a price-related target derivable from historical
  price data joined by ticker + timestamp — e.g., next-day return sign, realized
  volatility, or magnitude of price move in a window after `created`.
- Compare against baselines: a TF-IDF/bag-of-words probe and a random/majority
  baseline. If the embedding-only probe meaningfully beats the naive baselines, that's
  real evidence of price-relevant signal.
- Best option: run an ablation on the actual price prediction model — train once with
  embeddings + candles, once with candles only, and compare validation accuracy/loss.
  This is the ground-truth answer to whether the embeddings help.

This ablation-style probe requires joining the embeddings database with historical
price/candle data by ticker and date, and is not currently implemented in this repo.

## Planned Downstream Probe (`evaluate_downstream_probe.py`)

Not yet implemented — pending availability of historical price/candle data. Documented
here so the design is ready to build once that data source exists.

### Prerequisites
- Historical OHLCV candle data per ticker, at a granularity that allows computing a
  price change following an article's `created` timestamp (e.g., daily candles for a
  next-day-return target, or intraday candles for shorter horizons).
- A joinable key between `news_embeddings` (ticker via `ticker_symbols`, timestamp via
  `created`) and the candle dataset (ticker + date/datetime).

### Target Construction
For each article with a resolvable ticker and a candle price available after
`created`:
- **Classification target**: sign of return over a fixed horizon (e.g., next 1-day,
  3-day close-to-close return: up / down / flat within a small threshold band).
- **Regression target**: magnitude of return, or realized volatility over the horizon.
- Articles mentioning multiple tickers should either be exploded into one row per
  ticker or restricted to the primary/first ticker, to keep the label well-defined.

### Probe Models
- **Baseline features**: TF-IDF or bag-of-words vector of `title + teaser`, and a
  random/majority-class baseline, both fit with the same probe model for comparison.
- **Embedding-only probe**: logistic regression (classification) or ridge regression
  (regression target) trained on the FinBERT/sentence-transformer embedding as the
  sole input feature — no price/candle features — to isolate the embedding's signal.
- Use a simple, low-capacity model deliberately (linear/shallow) so results reflect
  the embedding's linearly-decodable signal rather than probe overfitting.

### Evaluation Protocol
- **Time-based train/test split** (not random shuffling) to avoid look-ahead bias,
  e.g., train on articles before a cutoff date, test on articles after it.
- Metrics: accuracy / AUC / F1 for classification targets, RMSE / R² for regression
  targets.
- Report embedding-probe metrics alongside the TF-IDF and random baselines from the
  same split, so the delta over baseline is the headline result.

### Final Ablation (Ground Truth for This Project)
Once the probe validates embeddings carry some signal, run the real ablation on the
actual price prediction model described in the project purpose:
- Train the full model once with `[embedding + candle features]`, once with
  `[candle features only]`, using identical splits and hyperparameters.
- Compare validation accuracy/loss between the two runs. An improvement from adding
  embeddings is the definitive evidence (not the proxy metrics in this document) that
  the embeddings are worth including in the trading model.
