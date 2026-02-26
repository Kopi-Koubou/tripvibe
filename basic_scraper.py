"""
Basic Scrapling Tutorial - Learning Core Concepts

This script demonstrates:
- Making requests with Fetcher
- CSS and XPath selectors
- Extracting text, attributes, and links
- Handling pagination
"""

from scrapling import Fetcher


def scrape_quotes():
    """Scrape quotes from quotes.toscrape.com with pagination."""
    fetcher = Fetcher()
    base_url = "https://quotes.toscrape.com"

    all_quotes = []
    page = 1

    while True:
        url = f"{base_url}/page/{page}/"
        print(f"\n--- Fetching page {page} ---")

        response = fetcher.get(url)

        if response.status != 200:
            print(f"Failed to fetch page {page}: status {response.status}")
            break

        # Find all quote containers using CSS selector
        quote_divs = response.css("div.quote")

        if not quote_divs:
            print("No more quotes found.")
            break

        for quote_div in quote_divs:
            # Extract quote text (CSS selector)
            text_elems = quote_div.css("span.text")
            text = text_elems[0].text if text_elems else ""

            # Extract author (CSS selector)
            author_elems = quote_div.css("small.author")
            author = author_elems[0].text if author_elems else ""

            # Extract tags
            tag_elems = quote_div.css("a.tag")
            tags = [tag.text for tag in tag_elems]

            quote_data = {
                "text": text,
                "author": author,
                "tags": tags
            }
            all_quotes.append(quote_data)

            # Print the quote
            print(f'\n"{text[:50]}..."')
            print(f"  - {author}")
            print(f"  Tags: {', '.join(tags)}")

        # Check for next page link
        next_btn = response.css("li.next a")
        if not next_btn:
            print("\nReached last page.")
            break

        page += 1

        # Limit to 3 pages for demo
        if page > 3:
            print("\nStopping at page 3 for demo purposes.")
            break

    print(f"\n=== Summary ===")
    print(f"Total quotes scraped: {len(all_quotes)}")

    # Show unique authors
    authors = set(q["author"] for q in all_quotes)
    print(f"Unique authors: {len(authors)}")

    return all_quotes


def demo_selectors():
    """Demonstrate various selector methods."""
    fetcher = Fetcher()
    response = fetcher.get("https://quotes.toscrape.com")

    print("\n=== Selector Demo ===\n")

    # CSS Selectors
    print("1. CSS Selectors:")
    quote_texts = response.css("div.quote span.text")
    if quote_texts:
        print(f"   First quote: {quote_texts[0].text[:50]}...")

    # Get attribute
    links = response.css("a")
    if links:
        print(f"   First link href: {links[0].attrib.get('href', 'N/A')}")

    # XPath Selectors
    print("\n2. XPath Selectors:")
    titles = response.xpath("//title")
    if titles:
        print(f"   Page title: {titles[0].text}")

    # Count elements
    all_quotes = response.css("div.quote")
    print(f"\n3. Element count: {len(all_quotes)} quotes on page")

    # Get all links
    all_links = response.css("a")
    print(f"   Total links: {len(all_links)}")


def test_httpbin():
    """Test request/response with httpbin.org."""
    fetcher = Fetcher()

    print("\n=== HTTPBin Tests ===\n")

    # Test GET request
    print("1. GET request:")
    response = fetcher.get("https://httpbin.org/get")
    print(f"   Status: {response.status}")

    # Test headers
    print("\n2. Headers test:")
    response = fetcher.get("https://httpbin.org/headers")
    print(f"   Status: {response.status}")

    # Test user agent
    print("\n3. User-Agent test:")
    response = fetcher.get("https://httpbin.org/user-agent")
    print(f"   Status: {response.status}")


if __name__ == "__main__":
    print("=" * 60)
    print("SCRAPLING BASIC TUTORIAL")
    print("=" * 60)

    # Run selector demo
    demo_selectors()

    # Test httpbin
    test_httpbin()

    # Scrape quotes with pagination
    quotes = scrape_quotes()
