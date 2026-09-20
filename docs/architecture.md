# Architecture

## Overview
This repository collects historical financial news from the Massive API (formerly
Benzinga) and encodes the articles into vector embeddings (FinBERT or
sentence-transformers) for semantic similarity search and downstream AI training
tasks (sentiment analysis, price prediction, trading signal research).

## Data Flow
```
Massive API (news endpoint)
  -> BenzingaNewsCollector.fetch_news()   [benzinga_collector.py]
       - cursor-based pagination (moves backward through time)
       - exponential backoff retry on 429/502/503/504
       - normalizes Benzinga vs. Massive response shapes
  -> collect_robust.collect_in_chunks()   [collect_robust.py]
       - splits large date ranges into 30-day chunks
       - checkpoint/resume + dedup by article ID
  -> JSON/CSV export (collector.save_to_json / save_to_csv)
  -> FinBERTEncoder                       [encode_with_finbert.py]
       - batch text encoding (title + teaser, or separately)
       - stores embeddings (float16) + metadata in SQLite
  -> example_encode_and_search.py
       - loads embeddings from SQLite, runs cosine-similarity search
```

## Components

### `benzinga_collector.py`
- `BenzingaNewsCollector` class: core API client.
- `BASE_URL = https://api.massive.com/benzinga/v2/news`; auth via `apiKey` query
  param (`BENZINGA_API_KEY` env var, loaded via `python-dotenv`).
- `fetch_news(days_back, tickers, channels, page_size=100, max_pages, date_from,
  date_to)`: paginates cursor-style, retries transient HTTP errors (3 retries,
  5s -> 10s -> 20s backoff), ~0.5s delay between requests.
- Internal field-extraction/adapter logic tolerates both the legacy Benzinga
  response shape and the newer wrapped Massive shape
  (`{"status": "OK", "results": [...]}`), including `tickers`/`channels` being
  plain string arrays instead of nested objects.
- `save_to_json` / `save_to_csv`: export helpers.

### `collect_robust.py`
- `collect_in_chunks(days_back, chunk_size_days=30, output_file, tickers,
  channels)`: wraps `BenzingaNewsCollector` to fetch large date ranges in
  30-day chunks, avoiding HTTP 504 timeouts on single large requests.
- Deduplicates articles across chunks/pages.

### `encode_with_finbert.py`
- `FinBERTEncoder` class, supports two `model_type` modes:
  - `finbert`: raw `ProsusAI/finbert` (HuggingFace `BertTokenizer` +
    `BertModel`), 768-dim embeddings, manual pooling.
  - `sentence-transformer`: `all-mpnet-base-v2` via `sentence-transformers`
    (default; 5-10x faster than raw FinBERT).
- Runs on GPU if available (`torch.cuda.is_available()`), else CPU.
- `encode_text` / batch encoding methods, and `encode_csv_to_sqlite(csv_path,
  db_path, model_type)` to persist embeddings + article metadata into SQLite
  (embeddings stored as pickled float16 arrays, ~100-150 bytes/article).
- Default text input combines title+teaser; a `--separate` CLI option encodes
  them independently.

### `example_encode_and_search.py` / `example_usage.py`
- Demonstrate loading embeddings from SQLite and running similarity search;
  usage demos, not automated tests (scenario blocks are commented out and
  meant to be uncommented before running).

### `run_*.py` scripts
- Pre-configured, pre-set-parameter wrappers around `collect_robust` /
  `benzinga_collector` for specific time ranges and/or ticker filters (e.g.
  `run_1year_complete.py`, `run_2months_complete.py`, `run_3months_complete.py`,
  `run_5year_complete.py`, `run_6months_complete.py`, `run_1year_tickers.py`).

### Manual validation scripts
- `probe_date_params.py`, `test_endpoints.py`, `test_custom_endpoint.py`,
  `quick_test.py`: interactive scripts for exploring/validating the API
  directly; run with `python <script>.py`. Not part of an automated test
  suite (no pytest/unittest in the repo).

### Data outputs
- `*.json` / `*.csv` files in the repo root (e.g. `test_sample.json`,
  `test_sample.csv`) are collected data outputs, not source code or fixtures.

## Technology Stack
- Collection: `requests`, `python-dotenv`, `pandas`
- Encoding: `transformers`, `torch`, `sentence-transformers`, `numpy`,
  `scikit-learn`
- Storage: `sqlite3` (stdlib), `pickle` (stdlib)
- Utilities: `tqdm`
- See [requirements.txt](../requirements.txt) for pinned version constraints.

## Key Constraints
- Max 100 results per page; cursor-based pagination required because the
  underlying dataset changes over time (not offset-based).
- Date ranges beyond ~30 days risk HTTP 504 timeouts from the API; use
  `collect_robust.py` chunking rather than a single large `fetch_news` call.
- Articles must be deduplicated by ID since the API can return repeats across
  pages/chunks.
- API migrated from `benzinga` to `massive.com`; code must keep supporting
  both the legacy and wrapped/new response shapes via the field-extraction
  adapter in `benzinga_collector.py`.
