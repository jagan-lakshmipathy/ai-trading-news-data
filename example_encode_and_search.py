"""
Simple example: Encode a small sample and test similarity search
Perfect for testing before running on full dataset
"""

import pandas as pd
from encode_with_finbert import FinBERTEncoder, encode_csv_to_sqlite, test_similarity_search

# Example 1: Quick test with test_sample.csv
print("=" * 80)
print("EXAMPLE 1: Encode test_sample.csv")
print("=" * 80)

# Encode the test sample
encode_csv_to_sqlite(
    csv_path='test_sample.csv',
    db_path='test_sample_embeddings.db',
    model_type='sentence-transformer',  # Faster, good quality
    combine_fields=True,  # Combine title + teaser
    batch_size=32,
    use_float16=True  # Save storage
)

print("\n✅ Encoding complete! Now testing similarity search...\n")

# Test similarity search
test_queries = [
    "Tesla earnings report",
    "Apple stock performance",
    "Oil prices rising",
    "AI technology news",
    "Cryptocurrency market"
]

for query in test_queries:
    print("\n" + "=" * 80)
    test_similarity_search('test_sample_embeddings.db', query, top_k=3)
    print("=" * 80)

# Example 2: Programmatic usage
print("\n\n" + "=" * 80)
print("EXAMPLE 2: Programmatic similarity search")
print("=" * 80)

import sqlite3
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity

# Load the database
conn = sqlite3.connect('test_sample_embeddings.db')
df = pd.read_sql('SELECT * FROM news_embeddings', conn)
conn.close()

# Decode embeddings
embeddings = np.array([pickle.loads(blob) for blob in df['combined_embedding']])

# Initialize encoder
encoder = FinBERTEncoder(model_type='sentence-transformer')

# Custom search function
def search_articles(query: str, top_k: int = 5):
    """Search for articles similar to query."""
    # Encode query
    query_emb = encoder.encode_text(query).astype(np.float16)
    
    # Calculate similarity
    sims = cosine_similarity([query_emb], embeddings)[0]
    
    # Get top results
    top_indices = sims.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        results.append({
            'score': float(sims[idx]),
            'title': df.iloc[idx]['title'],
            'teaser': df.iloc[idx]['teaser'][:100] + '...',
            'date': df.iloc[idx]['created'],
            'tickers': df.iloc[idx]['ticker_symbols']
        })
    return results

# Example searches
queries = [
    "SpaceX earnings",
    "Goldman Sachs ETF",
    "Trump policy changes"
]

for query in queries:
    print(f"\n🔍 Search: '{query}'")
    print("-" * 80)
    results = search_articles(query, top_k=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['score']:.3f}] {r['title']}")
        print(f"   Tickers: {r['tickers']}")

# Example 3: Find similar articles to a specific article
print("\n\n" + "=" * 80)
print("EXAMPLE 3: Find articles similar to a specific article")
print("=" * 80)

def find_similar_articles(article_id: int, top_k: int = 5):
    """Find articles similar to given article ID."""
    # Find article
    article_idx = df[df['id'] == article_id].index
    if len(article_idx) == 0:
        print(f"Article {article_id} not found")
        return
    
    article_idx = article_idx[0]
    source_article = df.iloc[article_idx]
    
    print(f"\nSource Article:")
    print(f"Title: {source_article['title']}")
    print(f"Date: {source_article['created']}")
    print(f"Tickers: {source_article['ticker_symbols']}")
    
    # Get embedding
    article_emb = embeddings[article_idx]
    
    # Find similar
    sims = cosine_similarity([article_emb], embeddings)[0]
    top_indices = sims.argsort()[-top_k-1:][::-1]
    
    print(f"\n📊 Top {top_k} Similar Articles:")
    print("-" * 80)
    
    for idx in top_indices:
        if idx == article_idx:
            continue  # Skip self
        score = sims[idx]
        similar = df.iloc[idx]
        print(f"\n[{score:.3f}] {similar['title']}")
        print(f"   Date: {similar['created']}")
        print(f"   Tickers: {similar['ticker_symbols']}")

# Find articles similar to the first article in dataset
first_article_id = df.iloc[0]['id']
find_similar_articles(first_article_id, top_k=5)

print("\n\n" + "=" * 80)
print("🎉 Examples complete!")
print("=" * 80)
print("\nNext steps:")
print("1. Run on full dataset: python encode_with_finbert.py --csv news_1year.csv --db news_1year.db")
print("2. Build a search API using Flask/FastAPI")
print("3. Create a recommendation system")
print("4. Use embeddings as features for trading models")
