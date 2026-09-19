"""
Quick test script - Use this once you know the correct API endpoint
"""

from benzinga_collector import BenzingaNewsCollector

# ============================================================
# STEP 1: Replace this with the correct Massive API endpoint
# ============================================================
# Check your Massive dashboard or API documentation for the correct URL
# Examples of what it might look like:
#   - https://api.massive.com/v1/news
#   - https://data.massive.com/api/news
#   - https://api.benzinga.com/v3/news (if they upgraded)
#   - or something completely different

MASSIVE_API_ENDPOINT = "https://YOUR_ENDPOINT_HERE"  # <-- CHANGE THIS

# ============================================================
# STEP 2: Run this script to test
# ============================================================

def test_custom_endpoint():
    """Test your custom endpoint."""
    print("Testing custom Massive API endpoint...")
    print(f"Endpoint: {MASSIVE_API_ENDPOINT}\n")
    
    try:
        # Initialize with custom endpoint
        collector = BenzingaNewsCollector(base_url=MASSIVE_API_ENDPOINT)
        
        # Try to fetch a small amount of data
        print("Fetching last 7 days of news (max 5 articles)...")
        articles = collector.fetch_news(
            days_back=7,
            page_size=5,
            max_pages=1
        )
        
        if articles:
            print(f"\n✅ SUCCESS! Retrieved {len(articles)} articles")
            print(f"\nFirst article:")
            print(f"  Title: {articles[0].get('title', 'N/A')}")
            print(f"  Date: {articles[0].get('created', 'N/A')}")
            print(f"  Tickers: {[t.get('symbol') for t in articles[0].get('tickers', [])]}")
            
            print(f"\n🎉 This endpoint works! Update BASE_URL in benzinga_collector.py to:")
            print(f'   BASE_URL = "{MASSIVE_API_ENDPOINT}"')
        else:
            print("⚠️  No articles returned. The endpoint might work but returned no data.")
            print("Try increasing days_back or checking if there's data available.")
            
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Verify the endpoint URL is correct")
        print("   2. Check your API key in the .env file")
        print("   3. Contact Massive support for help")
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")

if __name__ == '__main__':
    if "YOUR_ENDPOINT_HERE" in MASSIVE_API_ENDPOINT:
        print("=" * 60)
        print("⚠️  Please update MASSIVE_API_ENDPOINT in this file first!")
        print("=" * 60)
        print("\nSteps to find your endpoint:")
        print("1. Log into your Massive dashboard")
        print("2. Look for 'API' or 'API Documentation' section")
        print("3. Find the 'Base URL' or 'Endpoint' information")
        print("4. Update the MASSIVE_API_ENDPOINT variable above")
        print("\nCommon locations for API info:")
        print("- Account Settings > API")
        print("- Documentation > Getting Started")
        print("- Developer > API Keys")
    else:
        test_custom_endpoint()
