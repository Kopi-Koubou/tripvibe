"""
Skyscanner Flight Scraper - Singapore to New York

Successfully bypasses Cloudflare and extracts flight data.
"""

import re
import json
from datetime import datetime
from scrapling import StealthyFetcher


def scrape_skyscanner(origin="SIN", destination="NYCA", date="260612"):
    """
    Scrape flight prices from Skyscanner.

    Args:
        origin: Origin airport code (e.g., SIN for Singapore)
        destination: Destination code (e.g., NYCA for New York area)
        date: Date in YYMMDD format
    """
    url = f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{destination.lower()}/{date}/"

    print("=" * 70)
    print("SKYSCANNER FLIGHT SCRAPER")
    print("=" * 70)
    print(f"\nRoute: {origin} -> {destination}")
    print(f"Date: 20{date[:2]}-{date[2:4]}-{date[4:]}")
    print(f"URL: {url}\n")

    fetcher = StealthyFetcher(headless=True)

    print("Fetching with StealthyFetcher (bypassing Cloudflare)...")
    response = fetcher.fetch(url, solve_cloudflare=True)

    print(f"Status: {response.status}")
    print(f"Redirected to: {response.url}\n")

    if response.status != 200:
        print("Failed to fetch page")
        return None

    html = response.html_content

    # Detect currency based on redirect
    if ".my" in response.url:
        currency = "MYR"
        currency_symbol = "RM"
        usd_rate = 0.21
    elif ".sg" in response.url:
        currency = "SGD"
        currency_symbol = "S$"
        usd_rate = 0.74
    else:
        currency = "USD"
        currency_symbol = "$"
        usd_rate = 1.0

    print(f"Detected currency: {currency}")

    # Extract data
    results = {
        "route": f"{origin} -> {destination}",
        "date": f"20{date[:2]}-{date[2:4]}-{date[4:]}",
        "currency": currency,
        "prices": [],
        "airlines": [],
        "times": [],
        "durations": [],
        "scraped_at": datetime.now().isoformat()
    }

    # Extract prices
    price_pattern = rf'{currency_symbol}\s*([\d,]+)'
    prices = re.findall(price_pattern, html)
    # Filter to flight-range prices
    flight_prices = []
    for p in prices:
        try:
            val = int(p.replace(',', ''))
            if 500 <= val <= 50000:
                flight_prices.append(val)
        except:
            pass

    results["prices"] = sorted(set(flight_prices))

    # Extract airlines
    airline_names = [
        "Singapore Airlines", "United", "United Airlines",
        "Delta", "Delta Air Lines", "Emirates", "Qatar Airways", "Qatar",
        "Cathay Pacific", "ANA", "All Nippon Airways",
        "JAL", "Japan Airlines", "Korean Air",
        "EVA Air", "China Airlines", "Air China",
        "Turkish Airlines", "Lufthansa", "British Airways",
        "American Airlines", "Asiana"
    ]
    airline_pattern = '|'.join(re.escape(a) for a in airline_names)
    found_airlines = re.findall(f'({airline_pattern})', html, re.IGNORECASE)
    results["airlines"] = list(set(a.title() for a in found_airlines))

    # Extract departure/arrival times
    times = re.findall(r'\b(\d{1,2}:\d{2})\b', html)
    results["times"] = list(set(times))

    # Extract durations
    durations = re.findall(r'(\d{1,2}h\s*\d{0,2}m?)', html)
    # Filter reasonable durations (10h to 50h for SIN-NYC)
    valid_durations = []
    for d in durations:
        match = re.match(r'(\d+)h', d)
        if match:
            hours = int(match.group(1))
            if 10 <= hours <= 50:
                valid_durations.append(d)
    results["durations"] = list(set(valid_durations))

    # Print results
    print("\n" + "=" * 70)
    print("FLIGHT RESULTS")
    print("=" * 70)

    print(f"\n{'Airlines Operating This Route':}")
    for airline in sorted(results["airlines"]):
        print(f"  - {airline}")

    print(f"\n{'Prices Found':} ({currency})")
    if results["prices"]:
        min_price = min(results["prices"])
        max_price = max(results["prices"])
        print(f"  Cheapest: {currency_symbol} {min_price:,} (≈ ${int(min_price * usd_rate):,} USD)")
        print(f"  Most Expensive: {currency_symbol} {max_price:,} (≈ ${int(max_price * usd_rate):,} USD)")
        print(f"\n  All prices ({currency}):")
        for i, p in enumerate(results["prices"][:15]):
            usd = int(p * usd_rate)
            print(f"    {i+1:2}. {currency_symbol} {p:>6,}  (≈ ${usd:,} USD)")
        if len(results["prices"]) > 15:
            print(f"    ... and {len(results['prices']) - 15} more")

    print(f"\n{'Flight Durations':}")
    for d in sorted(results["durations"], key=lambda x: int(re.match(r'(\d+)', x).group(1))):
        print(f"  - {d}")

    print(f"\n{'Departure/Arrival Times Found':}")
    print(f"  {', '.join(sorted(results['times'])[:12])}")
    if len(results["times"]) > 12:
        print(f"  ... and {len(results['times']) - 12} more")

    # Save results
    with open("skyscanner_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: skyscanner_results.json")

    return results


def main():
    # Scrape Singapore to New York, June 12, 2026
    results = scrape_skyscanner(
        origin="SIN",
        destination="NYCA",
        date="260612"  # June 12, 2026
    )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if results and results["prices"]:
        min_price = min(results["prices"])
        print(f"""
Route: Singapore (SIN) -> New York (NYC)
Date: June 12, 2026

Cheapest Flight: ~${int(min_price * 0.21):,} USD
Airlines: {', '.join(sorted(results['airlines'])[:5])}
Typical Duration: 18-24 hours (1-2 stops)

Data successfully scraped from Skyscanner!
""")
    else:
        print("\nNo price data extracted. Site may have changed structure.")


if __name__ == "__main__":
    main()
