#!/usr/bin/env python3
"""
Collect 1 year for specific tickers only - MUCH faster!
"""
from collect_robust import collect_in_chunks

# Popular tech stocks
tickers = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META']

print(f"Collecting 1 year for tickers: {', '.join(tickers)}")
print("This will be MUCH faster than collecting all articles!\n")

articles = collect_in_chunks(
    days_back=365,
    chunk_size_days=30,
    tickers=tickers,
    output_file='news_1year_tech_stocks.json'
)

print(f"\n✅ Collected {len(articles):,} articles")

from benzinga_collector import BenzingaNewsCollector
collector = BenzingaNewsCollector()
collector.save_to_csv(articles, 'news_1year_tech_stocks.csv')
