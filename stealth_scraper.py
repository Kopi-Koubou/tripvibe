"""
StealthyFetcher Demo - Anti-Bot Bypass Features

This script demonstrates:
- Using StealthyFetcher for protected sites
- Cloudflare bypass options
- Headless browser mode
- Browser fingerprint options

Note: StealthyFetcher requires playwright browsers to be installed:
  playwright install chromium
"""

from scrapling import StealthyFetcher


def demo_stealthy_basic():
    """Basic StealthyFetcher usage."""
    print("\n=== Basic StealthyFetcher Demo ===\n")

    # Create a stealthy fetcher instance
    fetcher = StealthyFetcher(headless=True)

    # Fetch a page that might have bot detection
    print("Fetching quotes.toscrape.com with StealthyFetcher...")
    response = fetcher.fetch("https://quotes.toscrape.com")

    print(f"Status: {response.status}")

    # Extract some content to verify it worked
    quotes = response.css("div.quote")
    print(f"Found {len(quotes)} quotes")

    if quotes:
        text_elems = quotes[0].css("span.text")
        if text_elems:
            print(f"First quote: {text_elems[0].text[:60]}...")


def demo_cloudflare_bypass():
    """Demo Cloudflare bypass capability."""
    print("\n=== Cloudflare Bypass Demo ===\n")

    fetcher = StealthyFetcher(headless=True)

    # Test on a site with Cloudflare protection
    # Using httpbin as a safe test (no actual Cloudflare, but demonstrates the API)
    print("Testing StealthyFetcher with Cloudflare bypass option...")

    try:
        response = fetcher.fetch(
            "https://httpbin.org/html",
            solve_cloudflare=True,  # Enable Cloudflare solving
        )

        print(f"Status: {response.status}")

        # Check if we got content
        headings = response.css("h1")
        if headings:
            print(f"Page heading: {headings[0].text}")
        else:
            print("Page content received successfully")

    except Exception as e:
        print(f"Error (expected if no Cloudflare): {e}")


def demo_browser_options():
    """Demo various browser configuration options."""
    print("\n=== Browser Options Demo ===\n")

    # StealthyFetcher with custom options
    fetcher = StealthyFetcher(headless=True)

    # Test with books.toscrape.com
    print("Fetching books.toscrape.com...")
    response = fetcher.fetch("https://books.toscrape.com")

    print(f"Status: {response.status}")

    # Extract book information
    books = response.css("article.product_pod")
    print(f"Found {len(books)} books on the page")

    if books:
        for book in books[:3]:  # Show first 3
            title_elems = book.css("h3 a")
            price_elems = book.css("p.price_color")

            title = title_elems[0].attrib.get("title", "Unknown") if title_elems else "Unknown"
            price = price_elems[0].text if price_elems else "N/A"
            print(f"  - {title}: {price}")


def demo_wait_for_element():
    """Demo waiting for elements to load."""
    print("\n=== Wait for Element Demo ===\n")

    fetcher = StealthyFetcher(headless=True)

    # Fetch and wait for specific element
    print("Fetching with wait_selector...")

    try:
        response = fetcher.fetch(
            "https://quotes.toscrape.com",
            wait_selector="div.quote",  # Wait for quotes to load
        )

        print(f"Status: {response.status}")
        quotes = response.css("div.quote")
        print(f"Quotes loaded: {len(quotes)}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("STEALTHY FETCHER DEMO")
    print("=" * 60)
    print("\nNote: This requires playwright browsers to be installed.")
    print("Run: playwright install chromium\n")

    try:
        # Basic demo
        demo_stealthy_basic()

        # Browser options demo
        demo_browser_options()

        # Wait for element demo
        demo_wait_for_element()

        # Cloudflare bypass demo
        demo_cloudflare_bypass()

        print("\n" + "=" * 60)
        print("All StealthyFetcher demos completed!")
        print("=" * 60)

    except ImportError as e:
        print(f"\nImportError: {e}")
        print("\nPlease install playwright browsers:")
        print("  playwright install chromium")
    except Exception as e:
        print(f"\nError: {e}")
        print("StealthyFetcher may require additional setup.")
        print("Try running: playwright install chromium")
