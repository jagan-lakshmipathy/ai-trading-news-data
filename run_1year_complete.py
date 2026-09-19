#!/usr/bin/env python3
"""
Collect a complete year of news data using chunked collection
to avoid timeouts.
"""
from collect_robust import collect_in_chunks

print("=" * 70)
print("Collecting COMPLETE 1 YEAR of Benzinga news data")
print("Date range: August 2, 2025 - August 2, 2026")
print("Method: Chunked collection (30-day chunks)")
print("=" * 70)
print()

# Collect 1 year in 30-day chunks (12-13 chunks total)
articles = collect_in_chunks(
    days_back=365,
    chunk_size_days=30,
    output_file='news_complete_1year.json'
)

print()
print("=" * 70)
print(f"✅ COMPLETE! Collected {len(articles):,} articles")
print(f"Saved to: news_complete_1year.json")
print("=" * 70)

# Also save as CSV
from benzinga_collector import BenzingaNewsCollector
collector = BenzingaNewsCollector()
collector.save_to_csv(articles, 'news_complete_1year.csv')
print(f"Also saved as: news_complete_1year.csv")
