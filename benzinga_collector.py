"""
Massive (formerly Benzinga) Historical News Data Collector

This module provides functionality to collect historical news data from Massive API
(formerly Benzinga) with configurable date ranges and field selection.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import json
import time


class BenzingaNewsCollector:
    """Collector for Massive (formerly Benzinga) historical news data."""
    
    # Massive API endpoint (proxies Benzinga API)
    BASE_URL = "https://api.massive.com/benzinga/v2/news"
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Massive News Collector.
        
        Args:
            api_key: Massive API key. If not provided, will look for BENZINGA_API_KEY in environment.
            base_url: Optional custom API base URL. If not provided, uses the default Massive endpoint.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv('BENZINGA_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Massive API key is required. "
                "Set BENZINGA_API_KEY environment variable or pass api_key parameter."
            )
        
        # Allow custom base URL override
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = self.BASE_URL
        
        self.session = requests.Session()
        self.session.headers.update({'accept': 'application/json'})
    
    @staticmethod
    def _parse_date(value):
        """Parse a date string in various common formats into a datetime."""
        if isinstance(value, datetime):
            return value
        
        for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unrecognized date format: {value}")
    
    def fetch_news(
        self,
        days_back: int = 365,
        tickers: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
        include_body: bool = False,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical news data from Benzinga.
        
        Args:
            days_back: Number of days to look back (default: 365). Ignored if date_from is provided.
            tickers: List of stock tickers to filter by (e.g., ['AAPL', 'TSLA'])
            channels: List of channels to filter by (e.g., ['News', 'Earnings'])
            page_size: Number of results per page (max: 100)
            max_pages: Maximum number of pages to fetch (None for all)
            include_body: Whether to include full article body (uses more quota)
            date_from: Start date in format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
            date_to: End date in format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
        
        Returns:
            List of news articles with selected fields
        """
        # Calculate date range
        if date_to is None:
            date_to_dt = datetime.now()
        else:
            date_to_dt = self._parse_date(date_to)
        
        if date_from is None:
            date_from_dt = datetime.now() - timedelta(days=days_back)
        else:
            date_from_dt = self._parse_date(date_from)
        
        all_articles = []
        seen_ids = set()
        page = 0
        max_retries = 3
        
        # The API ignores 'page' and 'dateFrom'/'dateTo'; it supports cursor-based
        # pagination via 'published.gte'/'published.lte'. We narrow 'lte' down to
        # just before the oldest article seen in each batch to walk backwards
        # through history.
        cursor_lte = date_to_dt
        
        print(f"Fetching Massive news from {date_from_dt} to {date_to_dt}")
        print(f"Using API endpoint: {self.base_url}")
        
        while True:
            if max_pages and page >= max_pages:
                break
            
            if cursor_lte < date_from_dt:
                print("Reached start of requested date range")
                break
            
            params = {
                'apiKey': self.api_key,  # Massive uses 'apiKey' not 'token'
                'published.gte': date_from_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'published.lte': cursor_lte.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'pageSize': min(page_size, 100),  # API max is 100
                'displayOutput': 'full'
            }
            
            # Add optional filters
            if tickers:
                params['tickers'] = ','.join(tickers)
            
            if channels:
                params['channels'] = ','.join(channels)
            
            # Retry loop for handling timeouts
            retry_count = 0
            reached_end = False
            while retry_count <= max_retries:
                try:
                    response = self.session.get(self.base_url, params=params, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Massive API returns: {"status": "OK", "results": [...], "next_url": ...}
                    if isinstance(data, dict) and 'results' in data:
                        articles_data = data['results']
                    elif isinstance(data, list):
                        articles_data = data
                    else:
                        print(f"Unexpected response format at page {page}")
                        reached_end = True
                        break
                    
                    if not articles_data or len(articles_data) == 0:
                        print(f"No more results found at page {page}")
                        reached_end = True
                        break
                    
                    # Extract relevant fields
                    articles = self._extract_fields(articles_data, include_body)
                    
                    # Filter out articles we've already seen (API can repeat results
                    # instead of truly paginating for some date ranges)
                    new_articles = [a for a in articles if a.get('id') not in seen_ids]
                    
                    if not new_articles:
                        print(f"Page {page} returned no new articles (API repeating results). Stopping pagination.")
                        reached_end = True
                        break
                    
                    for a in new_articles:
                        seen_ids.add(a.get('id'))
                    all_articles.extend(new_articles)
                    
                    print(f"Fetched page {page}: {len(new_articles)} new articles (total: {len(all_articles)})")
                    
                    # Move the cursor to just before the oldest article in this batch
                    oldest = min(self._parse_date(a['created']) for a in new_articles if a.get('created'))
                    next_cursor = oldest - timedelta(seconds=1)
                    
                    # Check if we got fewer results than requested (last page)
                    if len(articles_data) < page_size:
                        print("Reached last page of results")
                        reached_end = True
                        break
                    
                    if next_cursor >= cursor_lte:
                        # Cursor didn't move; avoid an infinite loop
                        print("Cursor did not advance. Stopping pagination.")
                        reached_end = True
                        break
                    
                    cursor_lte = next_cursor
                    
                    # Success! Break out of retry loop and move to next page
                    page += 1
                    break  # Exit retry loop
                    
                except requests.exceptions.HTTPError as e:
                    status_code = response.status_code
                    
                    # Handle retryable errors (timeouts, server errors)
                    if status_code in [429, 502, 503, 504]:
                        retry_count += 1
                        if retry_count <= max_retries:
                            # Exponential backoff: 5s, 10s, 20s
                            wait_time = 5 * (2 ** (retry_count - 1))
                            
                            if status_code == 504:
                                print(f"Gateway timeout (504) on page {page}, retry {retry_count}/{max_retries}")
                            elif status_code == 503:
                                print(f"Service unavailable (503) on page {page}, retry {retry_count}/{max_retries}")
                            elif status_code == 502:
                                print(f"Bad gateway (502) on page {page}, retry {retry_count}/{max_retries}")
                            elif status_code == 429:
                                print(f"Rate limit (429) on page {page}, retry {retry_count}/{max_retries}")
                            
                            print(f"Waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                            continue  # Retry this page
                        else:
                            print(f"\nMax retries exceeded on page {page}. Saving {len(all_articles)} articles collected so far.")
                            print("You can resume collection later with a more specific date range.")
                            return all_articles  # Return what we have so far
                    
                    # Non-retryable errors
                    elif status_code == 401:
                        raise ValueError(
                            f"Invalid API key or incorrect endpoint. "
                            f"Current endpoint: {self.base_url}."
                        )
                    else:
                        print(f"HTTP Error {status_code}: {e}")
                        print(f"Response text: {response.text[:200]}")
                        raise
                        
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 5 * (2 ** (retry_count - 1))
                        print(f"Request timeout on page {page}, retry {retry_count}/{max_retries}")
                        print(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"\nMax retries exceeded due to timeouts on page {page}.")
                        print(f"Collected {len(all_articles)} articles so far.")
                        return all_articles
                        
                except Exception as e:
                    print(f"Error fetching page {page}: {e}")
                    # For unexpected errors, save what we have
                    if len(all_articles) > 0:
                        print(f"Returning {len(all_articles)} articles collected before error.")
                        return all_articles
                    reached_end = True
                    break
            
            if reached_end:
                break
            
            # Rate limiting between successful requests
            time.sleep(0.5)
        
        print(f"\nTotal articles collected: {len(all_articles)}")
        return all_articles
    
    def _extract_fields(self, articles: List[Dict], include_body: bool) -> List[Dict[str, Any]]:
        """
        Extract relevant fields from Massive API response.
        
        Args:
            articles: Raw article data from API
            include_body: Whether to include the full article body
        
        Returns:
            List of articles with selected fields
        """
        extracted = []
        
        for article in articles:
            # Tickers can be either a list of strings or list of dicts
            tickers_raw = article.get('tickers', []) or article.get('stocks', [])
            if tickers_raw and len(tickers_raw) > 0:
                if isinstance(tickers_raw[0], str):
                    # Massive returns simple string array: ["AAPL", "MSFT"]
                    tickers = [{'symbol': ticker, 'name': None} for ticker in tickers_raw]
                else:
                    # Old Benzinga format with nested objects
                    tickers = [
                        {
                            'name': ticker.get('name'),
                            'symbol': ticker.get('security', {}).get('symbol') if isinstance(ticker.get('security'), dict) else ticker.get('symbol')
                        }
                        for ticker in tickers_raw
                    ]
            else:
                tickers = []
            
            # Channels can be either a list of strings or list of dicts
            channels_raw = article.get('channels', [])
            if channels_raw and len(channels_raw) > 0:
                if isinstance(channels_raw[0], str):
                    # Massive returns simple string array: ["markets", "news"]
                    channels = channels_raw
                else:
                    # Old Benzinga format with nested objects
                    channels = [channel.get('name') for channel in channels_raw]
            else:
                channels = []
            
            # Same for categories
            categories_raw = article.get('categories', [])
            if categories_raw and len(categories_raw) > 0:
                if isinstance(categories_raw[0], str):
                    categories = categories_raw
                else:
                    categories = [cat.get('name') for cat in categories_raw]
            else:
                categories = []
            
            item = {
                # Essential fields (Massive uses different field names)
                'id': article.get('benzinga_id') or article.get('id'),  # Massive uses benzinga_id
                'created': article.get('published') or article.get('created'),  # Massive uses published
                'updated': article.get('last_updated') or article.get('updated'),  # Massive uses last_updated
                'title': article.get('title'),  # Headline
                'teaser': article.get('teaser'),  # Summary/teaser
                
                # Ticker information (essential)
                'tickers': tickers,
                
                # Categories and tags (useful)
                'channels': channels,
                'categories': categories,
                'tags': article.get('tags', []),
                
                # Optional fields
                'author': article.get('author'),
                'url': article.get('url'),
            }
            
            # Include body if requested (uses more API quota)
            if include_body:
                item['body'] = article.get('body')
            
            # Include images info (usually ignored but available)
            images_raw = article.get('images', [])
            if images_raw:
                if images_raw and len(images_raw) > 0 and isinstance(images_raw[0], str):
                    # Massive returns simple string array of URLs
                    item['images'] = [{'url': img} for img in images_raw]
                else:
                    # Old Benzinga format with nested objects
                    item['images'] = [
                        {
                            'size': img.get('size') if isinstance(img, dict) else None,
                            'url': img.get('url') if isinstance(img, dict) else img
                        }
                        for img in images_raw
                    ]
            
            extracted.append(item)
        
        return extracted
    
    def save_to_json(self, articles: List[Dict[str, Any]], filename: str):
        """
        Save articles to JSON file.
        
        Args:
            articles: List of articles to save
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(articles)} articles to {filename}")
    
    def save_to_csv(self, articles: List[Dict[str, Any]], filename: str):
        """
        Save articles to CSV file (flattens nested structures).
        
        Args:
            articles: List of articles to save
            filename: Output filename
        """
        import pandas as pd
        
        # Flatten the data for CSV
        flattened = []
        for article in articles:
            flat = article.copy()
            
            # Convert lists to strings for CSV
            if 'tickers' in flat:
                flat['ticker_symbols'] = ','.join([t.get('symbol', '') for t in flat['tickers'] if t.get('symbol')])
                flat['ticker_names'] = ','.join([t.get('name', '') for t in flat['tickers'] if t.get('name')])
                del flat['tickers']
            
            if 'channels' in flat:
                flat['channels'] = ','.join(flat['channels'])
            
            if 'categories' in flat:
                flat['categories'] = ','.join(flat['categories'])
            
            if 'tags' in flat:
                flat['tags'] = ','.join(flat['tags'])
            
            if 'images' in flat:
                del flat['images']  # Remove images for CSV
            
            flattened.append(flat)
        
        df = pd.DataFrame(flattened)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(articles)} articles to {filename}")


def main():
    """Example usage of the BenzingaNewsCollector."""
    
    # Initialize collector (try different endpoints if needed)
    # collector = BenzingaNewsCollector()  # Uses default endpoint
    # collector = BenzingaNewsCollector(base_url='https://api.massive.io/api/v2/news')  # Alternative endpoint
    collector = BenzingaNewsCollector()
    
    # Example 1: Fetch last year of news
    print("Example 1: Fetching last year of news")
    articles = collector.fetch_news(days_back=365, max_pages=5)
    
    # Example 2: Fetch news for specific tickers
    print("\nExample 2: Fetching news for AAPL and TSLA")
    articles = collector.fetch_news(
        days_back=30,
        tickers=['AAPL', 'TSLA'],
        max_pages=3
    )
    
    # Example 3: Fetch with custom date range
    print("\nExample 3: Fetching with custom date range")
    articles = collector.fetch_news(
        date_from='2024-01-01',
        date_to='2024-12-31',
        max_pages=5
    )
    
    # Save results
    if articles:
        collector.save_to_json(articles, 'benzinga_news.json')
        collector.save_to_csv(articles, 'benzinga_news.csv')


if __name__ == '__main__':
    main()
