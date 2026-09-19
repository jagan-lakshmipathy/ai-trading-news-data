"""
Test script to find the correct Massive API endpoint
"""

from benzinga_collector import BenzingaNewsCollector
import os
from dotenv import load_dotenv

# Explicitly load .env file
load_dotenv()

# List of possible Massive API endpoints to try
POSSIBLE_ENDPOINTS = [
    # Massive branded endpoints
    "https://data.massive.io/api/v1/news",
    "https://api.massive.io/api/v1/news",
    "https://api.massive.io/api/v2/news",
    "https://data.massive.io/api/v2/news",
    "https://api.getmassive.io/api/v1/news",
    "https://api.getmassive.io/api/v2/news",
    # Original Benzinga endpoints (in case auth method changed)
    "https://api.benzinga.com/api/v2/news",
    "https://api.benzinga.com/api/v2.1/news",
    # Alternative Massive domains
    "https://massive.com/api/v1/news",
    "https://api.massive.com/api/v1/news",
    "https://api.massive.com/api/v2/news",
    # Benzinga Pro
    "https://api.benzingapro.com/api/v2/news",
]

def test_endpoint(base_url):
    """Test a single endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing endpoint: {base_url}")
    print('='*60)
    
    try:
        collector = BenzingaNewsCollector(base_url=base_url)
        
        # Try to fetch just 1 article from the last 7 days
        articles = collector.fetch_news(
            days_back=7,
            page_size=1,
            max_pages=1
        )
        
        if articles and len(articles) > 0:
            print(f"✅ SUCCESS! This endpoint works!")
            print(f"Retrieved {len(articles)} article(s)")
            print(f"\nSample article:")
            print(f"  Title: {articles[0].get('title', 'N/A')}")
            print(f"  Date: {articles[0].get('created', 'N/A')}")
            return True
        else:
            print(f"❌ No articles returned (endpoint might work but no data)")
            return False
            
    except ValueError as e:
        print(f"❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return False

def main():
    """Test all possible endpoints."""
    print("Massive API Endpoint Finder")
    print("="*60)
    print("This script will test common Massive API endpoints")
    print("to find the correct one for your API key.")
    print("="*60)
    
    api_key = os.getenv('BENZINGA_API_KEY')
    if not api_key:
        print("\n❌ ERROR: BENZINGA_API_KEY not found in environment")
        print("Please set your Massive API key in the .env file")
        return
    
    print(f"\nAPI Key found: {api_key[:10]}...")
    
    working_endpoints = []
    
    for endpoint in POSSIBLE_ENDPOINTS:
        if test_endpoint(endpoint):
            working_endpoints.append(endpoint)
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if working_endpoints:
        print(f"\n✅ Found {len(working_endpoints)} working endpoint(s):")
        for endpoint in working_endpoints:
            print(f"   {endpoint}")
        
        print(f"\n📝 To use this endpoint, initialize the collector like this:")
        print(f'   collector = BenzingaNewsCollector(base_url="{working_endpoints[0]}")')
        
        print(f"\n📝 Or update the BASE_URL in benzinga_collector.py:")
        print(f'   BASE_URL = "{working_endpoints[0]}"')
    else:
        print("\n❌ No working endpoints found.")
        print("\n🔍 Troubleshooting steps:")
        print("   1. Verify your API key is correct in the .env file")
        print("   2. Check if your API key is active on the Massive dashboard")
        print("   3. Contact Massive support for the correct API endpoint")
        print("   4. Check Massive API documentation at https://massive.io or https://docs.massive.io")

if __name__ == '__main__':
    main()
