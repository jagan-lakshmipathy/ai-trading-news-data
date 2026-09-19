# FinBERT Encoding Guide

Complete guide to encode your Benzinga news CSV files with FinBERT embeddings.

## Quick Start

### Step 1: Install Dependencies

```bash
pip install transformers torch sentence-transformers pandas numpy scikit-learn tqdm
```

### Step 2: Run Encoding (Recommended Settings)

```bash
# Option A: Using sentence-transformer (RECOMMENDED - faster, better for similarity)
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model sentence-transformer

# Option B: Using raw FinBERT (slower, domain-specific)
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model finbert
```

### Step 3: Test Your Embeddings

```bash
# Search for similar articles
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model sentence-transformer \
    --test-query "Tesla earnings beat expectations"
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--csv` | Input CSV file path | **Required** |
| `--db` | Output SQLite database path | **Required** |
| `--model` | Model type: `finbert` or `sentence-transformer` | `sentence-transformer` |
| `--separate` | Encode title and teaser separately | Combined (title + teaser) |
| `--batch-size` | Batch size for encoding | 32 |
| `--no-float16` | Use float32 (more storage, slightly better precision) | float16 (recommended) |
| `--test-query` | Test query for similarity search | None |

## Model Comparison

### Sentence Transformer (Recommended)
```bash
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model sentence-transformer
```
- ✅ **Faster**: 5-10x faster encoding
- ✅ **Optimized** for semantic similarity
- ✅ **Smaller**: 768 dimensions
- ✅ **Better** for clustering and search
- ⚠️ General domain (not finance-specific)

**Time estimate**: 60K articles in ~15-30 minutes (GPU) or ~1-2 hours (CPU)

### Raw FinBERT
```bash
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model finbert
```
- ✅ **Financial** domain-specific
- ✅ Trained on financial text
- ⚠️ Slower encoding
- ⚠️ Not optimized for embeddings (trained for classification)

**Time estimate**: 60K articles in ~30-60 minutes (GPU) or ~2-4 hours (CPU)

## Advanced Usage

### 1. Encode Multiple CSV Files

```bash
# Encode each year separately
for year in {2022..2026}; do
    python encode_with_finbert.py \
        --csv news_${year}.csv \
        --db news_${year}_embeddings.db \
        --model sentence-transformer
done
```

### 2. Separate Title & Teaser Embeddings

```bash
# Store separate embeddings for title and teaser
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model sentence-transformer \
    --separate
```

Use when you want to:
- Search titles and teasers independently
- Weight title vs teaser differently
- Analyze which provides better signals

### 3. Full Precision (float32)

```bash
# Use float32 instead of float16 (2x storage, minimal accuracy gain)
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model sentence-transformer \
    --no-float16
```

### 4. Larger Batches (Faster with GPU)

```bash
# Increase batch size if you have GPU with lots of memory
python encode_with_finbert.py \
    --csv news_1year.csv \
    --db news_embeddings.db \
    --model sentence-transformer \
    --batch-size 128
```

## Output Database Schema

```sql
-- Main table with embeddings
CREATE TABLE news_embeddings (
    id INTEGER,
    created TEXT,
    updated TEXT,
    title TEXT,
    teaser TEXT,
    channels TEXT,
    categories TEXT,
    tags TEXT,
    author TEXT,
    url TEXT,
    ticker_symbols TEXT,
    ticker_names TEXT,
    combined_embedding BLOB,      -- pickled numpy array
    -- OR (if --separate flag used):
    -- title_embedding BLOB,
    -- teaser_embedding BLOB,
);

-- Metadata about encoding
CREATE TABLE encoding_metadata (
    model_type TEXT,
    embedding_dim INTEGER,
    combine_fields BOOLEAN,
    use_float16 BOOLEAN,
    total_articles INTEGER,
    encoded_at TEXT
);
```

## Using the Embeddings

### Query Similar Articles

```python
import sqlite3
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity

# Load database
conn = sqlite3.connect('news_embeddings.db')
df = pd.read_sql('SELECT * FROM news_embeddings', conn)

# Decode embeddings
embeddings = np.array([pickle.loads(blob) for blob in df['combined_embedding']])

# Encode your query
from encode_with_finbert import FinBERTEncoder
encoder = FinBERTEncoder(model_type='sentence-transformer')
query_emb = encoder.encode_text("Tesla stock surges on earnings")

# Find similar articles
similarities = cosine_similarity([query_emb], embeddings)[0]
top_5 = similarities.argsort()[-5:][::-1]

for idx in top_5:
    print(f"{similarities[idx]:.3f}: {df.iloc[idx]['title']}")
```

### Cluster Articles by Topic

```python
from sklearn.cluster import KMeans

# Cluster into 20 topics
kmeans = KMeans(n_clusters=20, random_state=42)
df['topic'] = kmeans.fit_predict(embeddings)

# See top articles per topic
for topic_id in range(20):
    topic_articles = df[df['topic'] == topic_id]
    print(f"\nTopic {topic_id}:")
    print(topic_articles[['title', 'ticker_symbols']].head())
```

### Find Articles Similar to a Given Article

```python
# Find articles similar to article ID 60862093
article_idx = df[df['id'] == 60862093].index[0]
article_emb = embeddings[article_idx]

similarities = cosine_similarity([article_emb], embeddings)[0]
similar_indices = similarities.argsort()[-6:][::-1][1:]  # Skip self

print("Similar articles:")
for idx in similar_indices:
    print(f"{similarities[idx]:.3f}: {df.iloc[idx]['title']}")
```

## Storage Estimates

| Dataset | Articles | Storage (float16) | Storage (float32) |
|---------|----------|------------------|------------------|
| 1 year | 60,000 | ~150 MB | ~300 MB |
| 5 years | 300,000 | ~700 MB | ~1.4 GB |
| 10 years | 600,000 | ~1.4 GB | ~2.8 GB |

*Includes original text + embeddings + indexes*

## Troubleshooting

### Out of Memory Error
```bash
# Reduce batch size
python encode_with_finbert.py --csv data.csv --db output.db --batch-size 16
```

### Slow on CPU
```bash
# Use sentence-transformer (faster)
# Or process in smaller chunks and combine databases later
```

### CUDA Not Available
```bash
# Script automatically falls back to CPU
# To force CPU: export CUDA_VISIBLE_DEVICES=""
```

## Next Steps

After encoding:
1. Build a semantic search API
2. Create a news recommendation system
3. Cluster articles by topic/sentiment
4. Train a trading signal model using embeddings as features
5. Build a RAG (Retrieval Augmented Generation) system for news Q&A

## Performance Tips

1. **Use GPU**: 10-20x faster than CPU
2. **Use sentence-transformer model**: 5x faster than raw FinBERT
3. **Use float16**: 50% less storage, negligible accuracy loss
4. **Increase batch_size**: Faster with more GPU memory
5. **Process in parallel**: Split CSV and encode chunks simultaneously
