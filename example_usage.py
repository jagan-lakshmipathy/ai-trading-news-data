"""
Example usage scenarios for Benzinga News Collector
"""

from benzinga_collector import BenzingaNewsCollector
from datetime import datetime, timedelta


def example_1_year_historical():
    """Collect 1 year of historical news data."""
    print("=" * 60)
    print("Example 1: Collecting 1 Year of Historical Data")
    print("=" * 60)
    
    collector = BenzingaNewsCollector()
    
    articles = collector.fetch_news(
        days_back=365,
        page_size=100,
        include_body=False  # Set to True if you need full article text
    )
    
    if articles:
        collector.save_to_json(articles, 'news_1year.json')
        collector.save_to_csv(articles, 'news_1year.csv')
        
        print(f"\nCollected {len(articles)} articles from the past year")
        print(f"Date range: {articles[-1]['created']} to {articles[0]['created']}")


def example_2_years_historical():
    """Collect 2 years of historical news data."""
    print("\n" + "=" * 60)
    print("Example 2: Collecting 2 Years of Historical Data")
    print("=" * 60)
    
    collector = BenzingaNewsCollector()
    
    articles = collector.fetch_news(
        days_back=730,  # 2 years
        page_size=100
    )
    
    if articles:
        collector.save_to_json(articles, 'news_2years.json')
        print(f"\nCollected {len(articles)} articles from the past 2 years")


def example_specific_tickers():
    """Collect news for specific stock tickers."""
    print("\n" + "=" * 60)
    print("Example 3: Collecting News for Specific Tickers")
    print("=" * 60)
    
    collector = BenzingaNewsCollector()
    
    # Tech stocks example
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']
    
    articles = collector.fetch_news(
        days_back=90,  # Last 3 months
        tickers=tickers,
        page_size=100
    )
    
    if articles:
        collector.save_to_json(articles, 'news_tech_stocks_90d.json')
        print(f"\nCollected {len(articles)} articles for tickers: {', '.join(tickers)}")


def example_custom_date_range():
    """Collect news for a specific custom date range."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Date Range (Q1 2024)")
    print("=" * 60)
    
    collector = BenzingaNewsCollector()
    
    articles = collector.fetch_news(
        date_from='2024-01-01',
        date_to='2024-03-31',
        page_size=100
    )
    
    if articles:
        collector.save_to_json(articles, 'news_q1_2024.json')
        print(f"\nCollected {len(articles)} articles for Q1 2024")


def example_with_channels():
    """Collect news filtered by specific channels."""
    print("\n" + "=" * 60)
    print("Example 5: News Filtered by Channels")
    print("=" * 60)
    
    collector = BenzingaNewsCollector()
    
    articles = collector.fetch_news(
        days_back=30,
        channels=['News', 'Earnings'],  # Focus on news and earnings reports
        page_size=100
    )
    
    if articles:
        collector.save_to_json(articles, 'news_filtered_channels.json')
        print(f"\nCollected {len(articles)} articles from News and Earnings channels")


def example_with_full_body():
    """Collect news with full article body (uses more API quota)."""
    print("\n" + "=" * 60)
    print("Example 6: News with Full Article Body")
    print("=" * 60)
    
    collector = BenzingaNewsCollector()
    
    articles = collector.fetch_news(
        days_back=7,
        tickers=['AAPL'],
        include_body=True,  # Include full article text
        max_pages=2  # Limit pages since body uses more quota
    )
    
    if articles:
        collector.save_to_json(articles, 'news_with_body.json')
        print(f"\nCollected {len(articles)} articles with full body text")


def example_analyze_collected_data():
    """Example of analyzing the collected data."""
    print("\n" + "=" * 60)
    print("Example 7: Analyzing Collected Data")
    print("=" * 60)
    
    collector = BenzingaNewsCollector()
    
    articles = collector.fetch_news(
        days_back=30,
        max_pages=5
    )
    
    if articles:
        # Analyze ticker distribution
        ticker_count = {}
        for article in articles:
            for ticker in article.get('tickers', []):
                symbol = ticker.get('symbol')
                if symbol:
                    ticker_count[symbol] = ticker_count.get(symbol, 0) + 1
        
        # Analyze channel distribution
        channel_count = {}
        for article in articles:
            for channel in article.get('channels', []):
                channel_count[channel] = channel_count.get(channel, 0) + 1
        
        print(f"\nTotal articles: {len(articles)}")
        print(f"\nTop 10 most mentioned tickers:")
        for ticker, count in sorted(ticker_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ticker}: {count} mentions")
        
        print(f"\nChannel distribution:")
        for channel, count in sorted(channel_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  {channel}: {count} articles")


if __name__ == '__main__':
    # Run all examples (comment out the ones you don't need)
    
    # Basic time-based collection
    example_1_year_historical()
    # example_2_years_historical()
    
    # Filtered collection
    # example_specific_tickers()
    # example_custom_date_range()
    # example_with_channels()
    
    # Advanced options
    # example_with_full_body()
    
    # Analysis
    # example_analyze_collected_data()
