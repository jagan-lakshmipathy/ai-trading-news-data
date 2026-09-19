#!/usr/bin/env python3
"""
Collect 2 months of news data using chunked collection
to avoid timeouts.
"""
from collect_robust import collect_in_chunks

print("=" * 70)
print("Collecting 2 MONTHS of Benzinga news data")
print("Date range: Last 60 days")
print("Method: Chunked collection (30-day chunks)")
print("=" * 70)
print()

# Collect 60 days in 30-day chunks (2 chunks total)
articles = collect_in_chunks(
    days_back=60,
    chunk_size_days=30,
    output_file='news_complete_2months.json'
)

print()
print("=" * 70)
print(f"✅ COMPLETE! Collected {len(articles):,} articles")
print(f"Saved to: news_complete_2months.json")
print("=" * 70)

# Also save as CSV
from benzinga_collector import BenzingaNewsCollector
collector = BenzingaNewsCollector()
collector.save_to_csv(articles, 'news_complete_2months.csv')
print(f"Also saved as: news_complete_2months.csv")
