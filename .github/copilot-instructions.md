# Copilot Instructions — ai-trading-news-data

## Project Purpose
Collects historical financial news (via the Massive API, formerly Benzinga) and encodes
articles with FinBERT / sentence-transformer embeddings for semantic similarity search and
AI training data (sentiment analysis, price prediction, trading signals research).

## Architecture / Data Flow
```
Massive API (news endpoint)
  -> BenzingaNewsCollector (benzinga_collector.py): pagination, retry, field normalization
  -> JSON/CSV export (news_complete_*.json/.csv)
  -> FinBERTEncoder (encode_with_finbert.py): batch embedding
  -> SQLite DB (pickled/float16 embeddings + metadata)
  -> similarity search / analysis (example_encode_and_search.py)
```

## Major Components
- `benzinga_collector.py` — core collector class: cursor-based pagination, exponential
  backoff retry (429/502/503/504), Benzinga↔Massive format adapter (`_extract_fields()`).
- `collect_robust.py` — chunked collection (30-day chunks) with checkpoint/resume and
  deduplication, used for large date ranges to avoid timeouts.
- `encode_with_finbert.py` — embedding pipeline: batch encoding, SQLite storage, metadata.
- `example_encode_and_search.py` / `example_usage.py` — usage demos (uncomment scenarios
  to run; not automated tests).
- `run_*.py` (e.g. `run_1year_complete.py`, `run_2months_complete.py`, `run_1year_tickers.py`)
  — pre-configured collection scripts for specific time ranges/ticker filters.
- `probe_date_params.py`, `test_endpoints.py`, `test_custom_endpoint.py`, `quick_test.py`
  — manual/interactive scripts for API exploration and validation.
- `*.json` / `*.csv` in repo root — collected data outputs, not source code (avoid editing
  or treating as fixtures).

## Important Interfaces
- API: `https://api.massive.com/benzinga/v2/news`, auth via `apiKey` query param, response
  shape `{"status": "OK", "results": [...]}`.
- Filters: `tickers` (comma-separated, e.g. `AAPL,TSLA`), `channels`, date range via
  `published.gte` / `published.lte`; pagination is cursor-based (moves backward through
  time), max 100 results/page.
- Key methods:
  - `collector.fetch_news(days_back=365, tickers=[...], channels=[...], max_pages=None)`
  - `collector.save_to_json(articles, path)` / `collector.save_to_csv(articles, path)`
  - `encoder.encode_batch(texts, batch_size=32)`
  - `encoder.encode_csv_to_sqlite(csv_path, db_path, model_type='sentence-transformer')`

## Coding Conventions
- Type hints used throughout (`Optional`, `List`, `Dict`, `Any`).
- Print-based logging with emoji status markers (✅ ❌ ⚠️ 📊) instead of the `logging` module.
- Config via `.env` (`BENZINGA_API_KEY`) loaded with `python-dotenv`.
- Retry/backoff pattern for transient HTTP errors: 3 retries, 5s→10s→20s.
- Format-adapter pattern to tolerate API field/shape changes (Benzinga vs. Massive).

## Testing Conventions
- No unit test framework (no pytest/unittest) — testing is done via runnable scripts.
- `quick_test.py`, `test_endpoints.py`, `test_custom_endpoint.py`, `probe_date_params.py`
  are interactive/manual validation tools, run directly with `python <script>.py`.
- Example scripts double as smoke tests (uncomment relevant scenario blocks before running).

## Dependencies
- Collection: `requests`, `python-dotenv`, `pandas`
- Encoding: `transformers`, `torch`, `sentence-transformers`, `numpy`, `scikit-learn`
- Storage: `sqlite3` (stdlib), `pickle` (stdlib)
- Utils: `tqdm`
- See `requirements.txt` for pinned versions.

## Important Constraints
- Rate limiting: ~0.5s delay between requests; 100 results max per page.
- Large date ranges (>~30 days) risk HTTP 504 timeouts — use chunked collection
  (`collect_robust.py`, 30-day chunks) rather than a single large `fetch_news` call.
- API migrated from `benzinga` to `massive.com`; response is now wrapped, and
  `tickers`/`channels` are plain string arrays (not nested objects) — code must keep
  supporting both shapes via the field-extraction adapter.
- Deduplicate collected articles by ID; the API can return repeated results across pages.
- Embeddings are stored as float16 to reduce storage (~100–150 bytes/article + metadata).

## Architectural Decisions to Preserve
- Cursor-based (not offset-based) pagination — required because the underlying dataset
  changes over time.
- Chunked 30-day collection with checkpoint/resume — specifically fixes 504 timeouts
  (see `TIMEOUT_FIX.md`).
- Default to `sentence-transformers` model type for encoding (5–10x faster than raw
  FinBERT) unless a task specifically needs raw FinBERT outputs.
- Default encoding combines title+teaser text; a `--separate` option exists for
  encoding them independently.
- SQLite + pickled embeddings chosen over an external vector DB for portability/simplicity
  — keep this dependency-light approach unless requirements change significantly.
