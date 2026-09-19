#!/usr/bin/env python3
"""
Collect a complete 5 years of news data using chunked collection
to avoid timeouts.
"""
from collect_robust import collect_in_chunks

print("=" * 70)
print("Collecting COMPLETE 5 YEARS of Benzinga news data")
print("Date range: August 23, 2021 - August 23, 2026")
print("Method: Chunked collection (30-day chunks)")
print("=" * 70)
print()

# Collect 5 years in 30-day chunks (~61 chunks total)
articles = collect_in_chunks(
    days_back=1825,
    chunk_size_days=30,
    output_file='news_complete_5year.json'
)

print()
print("=" * 70)
print(f"✅ COMPLETE! Collected {len(articles):,} articles")
print(f"Saved to: news_complete_5year.json")
print("=" * 70)

# Also save as CSV
from benzinga_collector import BenzingaNewsCollector
collector = BenzingaNewsCollector()
collector.save_to_csv(articles, 'news_complete_5year.csv')
print(f"Also saved as: news_complete_5year.csv")
