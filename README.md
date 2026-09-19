# Benzinga Historical News Data Collector

A Python tool for collecting historical news data from Massive (formerly Benzinga) API with configurable date ranges and comprehensive field extraction.

> **✅ STATUS: WORKING** - Successfully configured for Massive API!  
> See [QUICK_START.md](QUICK_START.md) for examples.

## Features

- ✅ Configurable historical data collection (1 year, 2 years, custom ranges)
- ✅ Comprehensive field extraction (all fields you specified)
- ✅ Multiple output formats (JSON, CSV)
- ✅ Ticker and channel filtering
- ✅ Automatic pagination and rate limiting
- ✅ Robust error handling
- ✅ Easy configuration via environment variables

## Prerequisites

1. **Massive API Key** (formerly Benzinga): You need an API key from Massive
   - Get your API key from [Massive](https://massive.com)
   - The API endpoint is already configured: `https://api.massive.com/benzinga/v2/news`

2. **Python 3.7+**

## Installation

1. Clone or navigate to this directory

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your Massive API key:
   ```
   BENZINGA_API_KEY=your_massive_api_key_here
   ```

5. **You're ready!** The correct endpoint is already configured.

## Usage

##Option 1: If you've updated BASE_URL in the code
collector = BenzingaNewsCollector()

# Option 2: Specify endpoint when creating collector
collector = BenzingaNewsCollector(base_url="https://your.massive.endpoint/api/v1/news"
```python
from benzinga_collector import BenzingaNewsCollector

# Initialize the collector
collector = BenzingaNewsCollector()

# Collect 1 year of historical data
articles = collector.fetch_news(days_back=365)

# Save to JSON
collector.save_to_json(articles, 'news_data.json')

# Save to CSV
collector.save_to_csv(articles, 'news_data.csv')
```

### Configuration Options

#### Time-Based Collection

```python
# Last 1 year
articles = collector.fetch_news(days_back=365)

# Last 2 years
articles = collector.fetch_news(days_back=730)

# Custom date range
articles = collector.fetch_news(
    date_from='2024-01-01',
    date_to='2024-12-31'
)

# Last 6 months
articles = collector.fetch_news(days_back=180)
```

#### Filtering

```python
# Filter by stock tickers
articles = collector.fetch_news(
    days_back=90,
    tickers=['AAPL', 'TSLA', 'NVDA']
)

# Filter by channels
articles = collector.fetch_news(
    days_back=30,
    channels=['News', 'Earnings']
)

# Combine filters
articles = collector.fetch_news(
    days_back=60,
    tickers=['AAPL'],
    channels=['News']
)
```

#### Advanced Options

```python
articles = collector.fetch_news(
    days_back=365,
    page_size=100,          # Results per page (max 100)
    max_pages=10,           # Limit number of pages
    include_body=True       # Include full article body (uses more quota)
)
```

### Run Examples

The repository includes comprehensive examples:

```bash
python example_usage.py
```

Edit `example_usage.py` to uncomment the examples you want to run.

## Data Fields

The collector extracts the following fields from Benzinga API:

### Essential Fields
- `id` - Benzinga article ID (for deduplication)
- `created` - Publication timestamp
- `updated` - Last updated timestamp
- `title` - Article headline
- `teaser` - Article summary/teaser
- `tickers` - Array of associated stock tickers with symbol and name

### Useful Fields
- `channels` - News channels/categories
- `categories` - Article categories
- `tags` - Article tags

### Optional Fields
- `author` - Article author
- `url` - Article URL
- `body` - Full article body (optional, set `include_body=True`)
- `images` - Article images (optional)

## Output Format

### JSON Output
```json
[
  {
    "id": "12345678",
    "created": "2024-01-15T09:30:00Z",
    "updated": "2024-01-15T09:30:00Z",
    "title": "Apple Announces New Product Line",
    "teaser": "Apple Inc. today announced...",
    "tickers": [
      {
        "name": "Apple Inc",
        "symbol": "AAPL"
      }
    ],
    "channels": ["News"],
    "categories": ["Technology"],
    "tags": ["Apple", "Product Launch"],
    "author": "John Doe",
    "url": "https://www.benzinga.com/..."
  }
]
```

### CSV Output
Flattened structure with ticker symbols and names in comma-separated columns.

## Rate Limiting

The collector includes automatic rate limiting:
- 0.5 second delay between requests
- Handles 429 (rate limit) errors with automatic retry
- Configurable `page_size` to control API quota usage

## Error Handling

- **Invalid API Key**: Raises `ValueError` with clear message
- **Rate Limits**: Automatically waits and retries
- **Network Errors**: Logs error and continues to next page
- **API Errors**: Comprehensive error messages with troubleshooting hints

## Best Practices

1. **Start Small**: Test with `max_pages=1` or `days_back=7` first
2. **Monitor Quota**: Full article bodies use more API quota
3. **Save Incrementally**: Save data periodically for large collections
4. **Use Filters**: Specify tickers/channels to reduce unnecessary data
5. **Check Date Ranges**: Verify your subscription tier supports the date range

## API Quota Considerations
or 401 Unauthorized Error
- **Most common issue**: Wrong API endpoint for Massive
- **Solution**: See [FIND_ENDPOINT.md](FIND_ENDPOINT.md) for detailed help
- Verify your API key in `.env` file
- Run `python test_endpoints.py` to auto-detect the endpoint
- Contact Massive support for the correct endpoint URLota
- Consider your Benzinga subscription tier limits
- Use `max_pages` to limit data collection during testing

## Troubleshooting

### "Invalid API key" Error
- Verify your API key in `.env` file
- Check that the key is active in your Benzinga account

### No Results Returned
- Check your date range is within your subscription limits
- Verify tickers/channels are valid
- Try reducing the `days_back` parameter

### Rate Limit Errors
- The collector handles this automatically
- If persistent, increase delay between requests in the code
- Contact Benzinga about your rate limits

## Example Workflows

### Collect 2 Years of Data for AI Training
```python
collector = BenzingaNewsCollector()

# Collect in chunks to avoid timeouts
for year in [2024, 2023]:
    articles = collector.fetch_news(
        date_from=f'{year}-01-01',
        date_to=f'{year}-12-31'
    )
    collector.save_to_json(articles, f'news_{year}.json')
```

### Monitor Specific Stocks
```python
collector = BenzingaNewsCollector()

watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

articles = collector.fetch_news(
    days_back=30,
    tickers=watchlist,
    channels=['News', 'Earnings']
)

collector.save_to_csv(articles, 'watchlist_news.csv')
```

## License

MIT License - Feel free to use and modify for your needs.

## Support

For API-related issues, contact Benzinga support.
For code issues, please check the error messages and troubleshooting section above.
