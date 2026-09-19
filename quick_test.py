#!/usr/bin/env python3
"""
Quick endpoint tester - paste any endpoint URL and test it immediately
"""

from benzinga_collector import BenzingaNewsCollector

def test_endpoint(endpoint_url):
    """Test a single endpoint URL."""
    print("=" * 70)
    print(f"Testing: {endpoint_url}")
    print("=" * 70)
    
    try:
        collector = BenzingaNewsCollector(base_url=endpoint_url)
        print("✓ Collector initialized\n")
        
        print("Fetching last 7 days of news (1 article)...")
        articles = collector.fetch_news(
            days_back=7,
            page_size=1,
            max_pages=1
        )
        
        if articles and len(articles) > 0:
            print(f"\n🎉 SUCCESS! This endpoint works!\n")
            article = articles[0]
            print(f"Sample article retrieved:")
            print(f"  ID: {article.get('id', 'N/A')}")
            print(f"  Title: {article.get('title', 'N/A')}")
            print(f"  Date: {article.get('created', 'N/A')}")
            tickers = [t.get('symbol') for t in article.get('tickers', [])]
            print(f"  Tickers: {tickers}")
            
            print(f"\n✅ UPDATE YOUR CODE:")
            print(f'   BASE_URL = "{endpoint_url}"')
            return True
        else:
            print("\n⚠️  No articles returned")
            print("   The endpoint might be correct but no data available")
            print("   Try increasing days_back or check if you have data access")
            return False
            
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Failed: {type(e).__name__}")
        print(f"   {str(e)[:200]}")
        return False

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("MASSIVE API ENDPOINT TESTER")
    print("=" * 70)
    print("\nPaste the endpoint URL from your Massive documentation below.")
    print("Examples:")
    print("  - https://api.example.com/v1/news")
    print("  - https://data.example.com/api/news")
    print("=" * 70)
    
    # Interactive mode
    try:
        endpoint = input("\nEndpoint URL: ").strip()
        
        if not endpoint:
            print("\n❌ No endpoint provided")
        elif not endpoint.startswith('http'):
            print("\n❌ Please include https:// in the URL")
        else:
            test_endpoint(endpoint)
            
    except KeyboardInterrupt:
        print("\n\nCancelled")
    except EOFError:
        # If running non-interactively, test some common patterns
        print("\n\nRunning in non-interactive mode.")
        print("Edit this script and set ENDPOINT_TO_TEST variable\n")
        
        # Add your endpoint here for testing
        ENDPOINT_TO_TEST = None  # e.g., "https://api.example.com/v1/news"
        
        if ENDPOINT_TO_TEST:
            test_endpoint(ENDPOINT_TO_TEST)
        else:
            print("Set ENDPOINT_TO_TEST in the script to test automatically")
