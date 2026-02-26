"""
Price Tracker - Book Price Monitoring Demo

This script demonstrates:
- Scraping product prices from books.toscrape.com
- Storing data in CSV format
- Comparing prices over time
- Basic alerting (console output)
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

from scrapling import Fetcher

# Data storage paths
DATA_DIR = Path(__file__).parent / "data"
PRICES_CSV = DATA_DIR / "book_prices.csv"
PRICES_JSON = DATA_DIR / "book_prices.json"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def scrape_book_prices(max_pages=2):
    """Scrape book prices from books.toscrape.com."""
    fetcher = Fetcher()
    base_url = "https://books.toscrape.com"

    all_books = []

    for page in range(1, max_pages + 1):
        if page == 1:
            url = f"{base_url}/index.html"
        else:
            url = f"{base_url}/catalogue/page-{page}.html"

        print(f"Scraping page {page}...")
        response = fetcher.get(url)

        if response.status != 200:
            print(f"Failed to fetch page {page}")
            continue

        books = response.css("article.product_pod")

        for book in books:
            # Extract title
            title_elems = book.css("h3 a")
            title = title_elems[0].attrib.get("title", "Unknown") if title_elems else "Unknown"

            # Extract relative URL
            href = title_elems[0].attrib.get("href", "") if title_elems else ""

            # Extract price (remove £ symbol)
            price_elems = book.css("p.price_color")
            price_text = price_elems[0].text if price_elems else "0"
            price = float(price_text.replace("£", "").strip())

            # Extract availability
            avail_elems = book.css("p.availability")
            availability = avail_elems[0].text.strip() if avail_elems else "Unknown"

            # Extract star rating
            rating_elems = book.css("p.star-rating")
            rating_class = rating_elems[0].attrib.get("class", "") if rating_elems else ""
            rating = rating_class.replace("star-rating ", "").strip()

            book_data = {
                "title": title,
                "price": price,
                "availability": availability,
                "rating": rating,
                "url": href,
                "scraped_at": datetime.now().isoformat()
            }
            all_books.append(book_data)

    print(f"Scraped {len(all_books)} books")
    return all_books


def load_previous_prices():
    """Load previously saved prices from JSON."""
    if not PRICES_JSON.exists():
        return {}

    with open(PRICES_JSON, "r") as f:
        data = json.load(f)

    # Convert to dict keyed by title for easy lookup
    return {book["title"]: book for book in data.get("books", [])}


def save_prices_csv(books):
    """Save book prices to CSV file."""
    ensure_data_dir()

    # Check if file exists to determine if we need header
    file_exists = PRICES_CSV.exists()

    with open(PRICES_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["title", "price", "availability", "rating", "scraped_at"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for book in books:
            writer.writerow({k: book[k] for k in fieldnames})

    print(f"Saved {len(books)} records to {PRICES_CSV}")


def save_prices_json(books):
    """Save book prices to JSON file (overwrites with latest)."""
    ensure_data_dir()

    data = {
        "last_updated": datetime.now().isoformat(),
        "count": len(books),
        "books": books
    }

    with open(PRICES_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(books)} records to {PRICES_JSON}")


def compare_prices(current_books, previous_prices):
    """Compare current prices with previous and alert on changes."""
    print("\n" + "=" * 60)
    print("PRICE COMPARISON REPORT")
    print("=" * 60 + "\n")

    if not previous_prices:
        print("No previous prices to compare (first run).")
        return

    changes = []
    new_books = []

    for book in current_books:
        title = book["title"]
        current_price = book["price"]

        if title in previous_prices:
            prev_price = previous_prices[title]["price"]

            if current_price != prev_price:
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100

                changes.append({
                    "title": title,
                    "old_price": prev_price,
                    "new_price": current_price,
                    "change": change,
                    "change_pct": change_pct
                })
        else:
            new_books.append(book)

    # Report price changes
    if changes:
        print("PRICE CHANGES DETECTED:\n")

        # Sort by change percentage
        changes.sort(key=lambda x: x["change_pct"])

        for c in changes:
            direction = "DROPPED" if c["change"] < 0 else "INCREASED"
            print(f"{direction}: {c['title'][:40]}...")
            print(f"   {c['old_price']:.2f} -> {c['new_price']:.2f} ({c['change_pct']:+.1f}%)")
            print()
    else:
        print("No price changes detected.\n")

    # Report new books
    if new_books:
        print(f"NEW BOOKS FOUND: {len(new_books)}\n")
        for book in new_books[:5]:  # Show first 5
            print(f"   - {book['title'][:40]}... - {book['price']:.2f}")
        if len(new_books) > 5:
            print(f"   ... and {len(new_books) - 5} more")

    print("\n" + "=" * 60)


def show_statistics(books):
    """Display basic statistics about scraped books."""
    print("\nSTATISTICS:\n")

    prices = [b["price"] for b in books]

    print(f"   Total books: {len(books)}")
    print(f"   Price range: {min(prices):.2f} - {max(prices):.2f}")
    print(f"   Average price: {sum(prices)/len(prices):.2f}")

    # Rating distribution
    ratings = {}
    for book in books:
        r = book["rating"]
        ratings[r] = ratings.get(r, 0) + 1

    print(f"\n   Rating distribution:")
    for rating in ["One", "Two", "Three", "Four", "Five"]:
        count = ratings.get(rating, 0)
        bar = "#" * (count // 2)
        print(f"   {rating:6} {bar} ({count})")


def main():
    """Main price tracker workflow."""
    print("=" * 60)
    print("BOOK PRICE TRACKER")
    print("=" * 60)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load previous prices for comparison
    previous_prices = load_previous_prices()
    if previous_prices:
        print(f"Loaded {len(previous_prices)} previous price records.\n")

    # Scrape current prices
    print("Scraping current prices from books.toscrape.com...\n")
    books = scrape_book_prices(max_pages=2)

    if not books:
        print("No books scraped. Exiting.")
        return

    # Show statistics
    show_statistics(books)

    # Compare with previous prices
    compare_prices(books, previous_prices)

    # Save to both CSV (append) and JSON (overwrite)
    save_prices_csv(books)
    save_prices_json(books)

    print("\nPrice tracking complete!")
    print(f"\nRun again to see price changes over time.")


if __name__ == "__main__":
    main()
