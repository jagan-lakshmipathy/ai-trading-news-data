"""
Robust data collection with automatic chunking for large date ranges.
Useful when collecting 1+ years of data to avoid timeouts.
"""

from benzinga_collector import BenzingaNewsCollector
from datetime import datetime, timedelta
import json


def collect_in_chunks(
    days_back=365,
    chunk_size_days=30,
    output_file='news_data.json',
    tickers=None,
    channels=None
):
    """
    Collect historical data in chunks to avoid timeouts.
    
    Args:
        days_back: Total number of days to collect
        chunk_size_days: Size of each chunk (default: 30 days)
        output_file: Output filename
        tickers: Optional list of tickers to filter
        channels: Optional list of channels to filter
    """
    collector = BenzingaNewsCollector()
    all_articles = []
    
    # Calculate date ranges
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    current_start = start_date
    chunk_num = 0
    
    print("=" * 70)
    print(f"Collecting {days_back} days of data in {chunk_size_days}-day chunks")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print("=" * 70)
    
    while current_start < end_date:
        chunk_num += 1
        current_end = min(current_start + timedelta(days=chunk_size_days), end_date)
        
        print(f"\nChunk {chunk_num}: {current_start.date()} to {current_end.date()}")
        
        try:
            articles = collector.fetch_news(
                date_from=current_start.strftime('%Y-%m-%d'),
                date_to=current_end.strftime('%Y-%m-%d'),
                tickers=tickers,
                channels=channels,
                max_pages=None  # Collect all pages in this chunk
            )
            
            all_articles.extend(articles)
            print(f"  Collected {len(articles)} articles (total: {len(all_articles)})")
            
            # Save progress after each chunk
            if len(all_articles) > 0:
                temp_file = f"{output_file}.chunk{chunk_num}.json"
                with open(temp_file, 'w') as f:
                    json.dump(articles, f, indent=2)
                print(f"  Saved chunk to {temp_file}")
            
        except Exception as e:
            print(f"  Error in chunk {chunk_num}: {e}")
            print(f"  Continuing with next chunk...")
        
        current_start = current_end
    
    # Deduplicate across chunk boundaries (chunks can overlap by a second or two)
    if all_articles:
        seen_ids = set()
        deduped = []
        for article in all_articles:
            article_id = article.get('id')
            if article_id in seen_ids:
                continue
            seen_ids.add(article_id)
            deduped.append(article)
        
        if len(deduped) < len(all_articles):
            print(f"\nRemoved {len(all_articles) - len(deduped)} duplicate articles from chunk boundaries")
        
        all_articles = deduped
    
    # Save final combined file
    if all_articles:
        collector.save_to_json(all_articles, output_file)
        collector.save_to_csv(all_articles, output_file.replace('.json', '.csv'))
        
        print("\n" + "=" * 70)
        print(f"✅ Collection complete!")
        print(f"Total articles: {len(all_articles)}")
        print(f"Saved to: {output_file}")
        print("=" * 70)
    else:
        print("\n⚠️  No articles collected")
    
    return all_articles


def collect_with_resume(
    days_back=365,
    output_file='news_data.json',
    checkpoint_file='checkpoint.json'
):
    """
    Collect data with resume capability.
    If interrupted, can resume from the last checkpoint.
    """
    import os
    
    collector = BenzingaNewsCollector()
    
    # Check for existing checkpoint
    start_page = 0
    all_articles = []
    
    if os.path.exists(checkpoint_file):
        print(f"Found checkpoint file: {checkpoint_file}")
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                start_page = checkpoint.get('last_page', 0) + 1
                
                # Load existing articles
                if os.path.exists(checkpoint['data_file']):
                    with open(checkpoint['data_file'], 'r') as df:
                        all_articles = json.load(df)
                
                print(f"Resuming from page {start_page} ({len(all_articles)} articles already collected)")
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            print("Starting fresh...")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    print(f"\nCollecting data from {start_date.date()} to {end_date.date()}")
    
    page = start_page
    max_pages_per_checkpoint = 50  # Save checkpoint every 50 pages
    
    try:
        while True:
            print(f"\nFetching page {page}...")
            
            articles = collector.fetch_news(
                date_from=start_date.strftime('%Y-%m-%d'),
                date_to=end_date.strftime('%Y-%m-%d'),
                page_size=100,
                max_pages=page + 1  # Fetch one page at a time
            )
            
            if not articles or len(articles) <= len(all_articles):
                print("No more pages to fetch")
                break
            
            # Add only new articles
            new_articles = articles[len(all_articles):]
            all_articles.extend(new_articles)
            
            print(f"  Added {len(new_articles)} articles (total: {len(all_articles)})")
            
            # Save checkpoint every N pages
            if page % max_pages_per_checkpoint == 0:
                checkpoint = {
                    'last_page': page,
                    'data_file': output_file,
                    'timestamp': datetime.now().isoformat()
                }
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint, f, indent=2)
                
                collector.save_to_json(all_articles, output_file)
                print(f"  💾 Checkpoint saved at page {page}")
            
            page += 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        print(f"Saving checkpoint at page {page}...")
        
        checkpoint = {
            'last_page': page,
            'data_file': output_file,
            'timestamp': datetime.now().isoformat()
        }
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print(f"Saving progress at page {page}...")
    
    # Final save
    if all_articles:
        collector.save_to_json(all_articles, output_file)
        collector.save_to_csv(all_articles, output_file.replace('.json', '.csv'))
        print(f"\n✅ Saved {len(all_articles)} articles to {output_file}")
    
    # Clean up checkpoint
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print("Checkpoint file removed")
    
    return all_articles


if __name__ == '__main__':
    # Example 1: Collect 1 year in 30-day chunks
    print("Example 1: Collecting 1 year in chunks")
    articles = collect_in_chunks(
        days_back=365,
        chunk_size_days=30,
        output_file='news_1year_chunked.json'
    )
    
    # Example 2: Collect 2 years for specific tickers
    # articles = collect_in_chunks(
    #     days_back=730,
    #     chunk_size_days=30,
    #     tickers=['AAPL', 'TSLA', 'NVDA'],
    #     output_file='tech_stocks_2years.json'
    # )
    
    # Example 3: Resumable collection
    # articles = collect_with_resume(
    #     days_back=365,
    #     output_file='news_resumable.json',
    #     checkpoint_file='collection_checkpoint.json'
    # )
