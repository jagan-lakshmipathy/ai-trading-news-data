# How to Find Your Massive API Endpoint

Since Benzinga has transitioned to Massive, the API endpoint has changed. Here's how to find the correct endpoint:

## Steps to Find Your Endpoint

### 1. Check Your Massive Dashboard

Log into your Massive account and look for:
- **Settings** → **API** section
- **Developer** → **API Keys** or **API Documentation**
- **Account** → **API Access**

The endpoint will typically be shown as:
- "Base URL"
- "API Endpoint"
- "API Base URL"

### 2. Check Documentation

Look for:
- Getting Started guide
- API Documentation
- Quick Start guide
- Developer Documentation

### 3. Common Endpoint Patterns

The endpoint might look like one of these:
```
https://api.massive.com/v1/news
https://data.massive.com/v1/news
https://api.massive.com/api/news
https://massive.com/api/v1/news
https://api.benzinga.com/v3/news  (if upgraded version)
```

### 4. Contact Support

If you can't find it:
- Email: support@massive.com or api-support@massive.com
- Ask: "What is the base URL for the News API endpoint?"

## Once You Have the Endpoint

### Option 1: Update the Code (Permanent)

Edit [benzinga_collector.py](benzinga_collector.py) line 19:

```python
BASE_URL = "https://YOUR_ACTUAL_ENDPOINT_HERE"
```

### Option 2: Pass it When Creating Collector (Temporary)

```python
from benzinga_collector import BenzingaNewsCollector

collector = BenzingaNewsCollector(base_url="https://YOUR_ACTUAL_ENDPOINT_HERE")
articles = collector.fetch_news(days_back=365)
```

### Option 3: Use the Test Script

1. Edit [test_custom_endpoint.py](test_custom_endpoint.py)
2. Update the `MASSIVE_API_ENDPOINT` variable
3. Run: `python test_custom_endpoint.py`

## What We Know So Far

✅ Your API key format looks correct: `0i1t3RBYiB5sKY9Bl1eiJ_sT1foBRFS3`
❌ These domains don't work:
- `api.massive.io` (DNS doesn't resolve)
- `data.massive.io` (DNS doesn't resolve)
- `api.benzinga.com` (rejects your Massive API key)

✅ `massive.com` exists - so the endpoint is likely under this domain

## Need Help?

Run the automated endpoint finder (tries multiple patterns):
```bash
python test_endpoints.py
```

Or use the custom endpoint tester once you know the URL:
```bash
python test_custom_endpoint.py
```
