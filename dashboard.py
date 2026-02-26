"""
Flight Price Dashboard - Skyscanner Scraper UI

A simple Flask dashboard to search and display flight prices.
"""

import json
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from scrapling import StealthyFetcher

app = Flask(__name__)

# Store results in memory and file
RESULTS_FILE = Path(__file__).parent / "flight_results.json"

# Common airport codes
AIRPORTS = {
    "SIN": "Singapore",
    "NYCA": "New York (All)",
    "JFK": "New York JFK",
    "EWR": "Newark",
    "LAX": "Los Angeles",
    "SFO": "San Francisco",
    "LHR": "London Heathrow",
    "CDG": "Paris CDG",
    "NRT": "Tokyo Narita",
    "HND": "Tokyo Haneda",
    "HKG": "Hong Kong",
    "BKK": "Bangkok",
    "DXB": "Dubai",
    "SYD": "Sydney",
    "ICN": "Seoul Incheon",
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Price Tracker</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .search-box {
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .search-form {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr auto;
            gap: 20px;
            align-items: end;
        }
        .form-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-size: 0.9em; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
        select, input {
            padding: 15px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.15);
            color: #fff;
            font-size: 1em;
        }
        select option { background: #1a1a2e; }
        button {
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            color: #fff;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,212,255,0.3); }
        button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .results {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .route-info h2 { font-size: 1.8em; margin-bottom: 5px; }
        .route-info .meta { color: #888; font-size: 0.9em; }
        .best-price {
            text-align: right;
        }
        .best-price .label { color: #888; font-size: 0.8em; text-transform: uppercase; }
        .best-price .price {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(90deg, #00ff88, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
        }
        .stat-card .label { color: #888; font-size: 0.85em; margin-bottom: 8px; }
        .stat-card .value { font-size: 1.4em; font-weight: bold; }
        .airlines-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 30px;
        }
        .airline-tag {
            background: rgba(123, 44, 191, 0.3);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th { color: #888; font-weight: normal; text-transform: uppercase; font-size: 0.85em; }
        tr:hover { background: rgba(255,255,255,0.05); }
        .price-cell { font-weight: bold; color: #00ff88; }
        .loading {
            text-align: center;
            padding: 60px;
            color: #888;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #00d4ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .no-results {
            text-align: center;
            padding: 60px;
            color: #666;
        }
        .cost-info {
            background: rgba(0, 212, 255, 0.1);
            border-left: 4px solid #00d4ff;
            padding: 15px 20px;
            margin-top: 20px;
            border-radius: 0 8px 8px 0;
            font-size: 0.9em;
        }
        .cost-info strong { color: #00d4ff; }
        @media (max-width: 768px) {
            .search-form { grid-template-columns: 1fr; }
            .results-header { flex-direction: column; gap: 20px; text-align: center; }
            .best-price { text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Flight Price Tracker</h1>

        <div class="search-box">
            <form class="search-form" id="searchForm">
                <div class="form-group">
                    <label>From</label>
                    <select name="origin" id="origin">
                        {% for code, name in airports.items() %}
                        <option value="{{ code }}" {% if code == 'SIN' %}selected{% endif %}>{{ code }} - {{ name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>To</label>
                    <select name="destination" id="destination">
                        {% for code, name in airports.items() %}
                        <option value="{{ code }}" {% if code == 'NYCA' %}selected{% endif %}>{{ code }} - {{ name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>Date</label>
                    <input type="date" name="date" id="date" value="{{ default_date }}">
                </div>
                <button type="submit" id="searchBtn">Search Flights</button>
            </form>
        </div>

        <div id="resultsContainer">
            {% if results %}
            <div class="results">
                <div class="results-header">
                    <div class="route-info">
                        <h2>{{ results.route }}</h2>
                        <div class="meta">{{ results.date }} | Scraped {{ results.scraped_at[:19] }}</div>
                    </div>
                    <div class="best-price">
                        <div class="label">Best Price</div>
                        <div class="price">${{ results.min_usd }}</div>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="label">Price Range ({{ results.currency }})</div>
                        <div class="value">{{ results.currency_symbol }}{{ results.prices[0] }} - {{ results.currency_symbol }}{{ results.prices[-1] }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Airlines Found</div>
                        <div class="value">{{ results.airlines|length }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Shortest Flight</div>
                        <div class="value">{{ results.shortest_duration }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Price Points</div>
                        <div class="value">{{ results.prices|length }}</div>
                    </div>
                </div>

                <h3 style="margin-bottom: 15px; color: #aaa;">Airlines</h3>
                <div class="airlines-list">
                    {% for airline in results.airlines|sort %}
                    <span class="airline-tag">{{ airline }}</span>
                    {% endfor %}
                </div>

                <h3 style="margin-bottom: 15px; color: #aaa;">Price Breakdown</h3>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Price ({{ results.currency }})</th>
                            <th>Price (USD)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for price in results.prices[:20] %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td>{{ results.currency_symbol }}{{ "{:,}".format(price) }}</td>
                            <td class="price-cell">${{ "{:,}".format((price * results.usd_rate)|int) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% if results.prices|length > 20 %}
                <p style="text-align: center; color: #666; margin-top: 15px;">
                    ... and {{ results.prices|length - 20 }} more price points
                </p>
                {% endif %}

                <div class="cost-info">
                    <strong>Scraping Cost:</strong> This search used ~5-10 sec CPU, ~2MB bandwidth.
                    No API fees - direct browser automation via Scrapling/Playwright.
                    Commercial flight APIs (Amadeus, etc.) charge $0.01-0.05 per query.
                </div>
            </div>
            {% else %}
            <div class="no-results">
                <p>Enter search parameters above and click "Search Flights" to scrape Skyscanner.</p>
                <p style="margin-top: 10px; font-size: 0.9em;">First search may take 10-15 seconds due to browser startup.</p>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('searchBtn');
            const container = document.getElementById('resultsContainer');

            btn.disabled = true;
            btn.textContent = 'Scraping...';

            container.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Fetching flight data from Skyscanner...</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">This may take 10-20 seconds</p>
                </div>
            `;

            const origin = document.getElementById('origin').value;
            const destination = document.getElementById('destination').value;
            const date = document.getElementById('date').value;

            try {
                const response = await fetch(`/api/search?origin=${origin}&destination=${destination}&date=${date}`);
                const data = await response.json();

                if (data.error) {
                    container.innerHTML = `<div class="no-results"><p>Error: ${data.error}</p></div>`;
                } else {
                    location.reload();
                }
            } catch (err) {
                container.innerHTML = `<div class="no-results"><p>Error: ${err.message}</p></div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Search Flights';
            }
        });
    </script>
</body>
</html>
"""


def scrape_flights(origin, destination, date_str):
    """Scrape flight prices from Skyscanner."""
    # Convert date to Skyscanner format (YYMMDD)
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    sky_date = date_obj.strftime("%y%m%d")

    # Force Singapore locale for SGD pricing
    url = f"https://www.skyscanner.com.sg/transport/flights/{origin.lower()}/{destination.lower()}/{sky_date}/?currency=SGD&locale=en-GB&market=SG"

    fetcher = StealthyFetcher(headless=True)
    response = fetcher.fetch(url, solve_cloudflare=True)

    if response.status != 200:
        return None

    html = response.html_content

    # Detect currency - default to SGD
    if ".my" in response.url and "SGD" not in response.url:
        currency, symbol, rate = "MYR", "RM ", 0.21
    else:
        # Singapore dollars
        currency, symbol, rate = "SGD", "S$", 0.75

    # Extract prices - Singapore site uses $ without S prefix
    price_pattern = r'\$\s*([\d,]+)'
    matches = re.findall(price_pattern, html)
    flight_prices = []
    for p in matches:
        try:
            val = int(p.replace(',', ''))
            if 400 <= val <= 20000:  # SGD flight price range
                flight_prices.append(val)
        except:
            pass

    # Extract airlines
    airline_names = [
        "Singapore Airlines", "United", "Delta", "Emirates", "Qatar Airways",
        "Cathay Pacific", "ANA", "All Nippon Airways", "JAL", "Japan Airlines",
        "Korean Air", "EVA Air", "China Airlines", "Air China", "Turkish Airlines",
        "Lufthansa", "British Airways", "American Airlines", "Asiana"
    ]
    found_airlines = set()
    for airline in airline_names:
        if airline.lower() in html.lower():
            found_airlines.add(airline)

    # Extract durations
    durations = re.findall(r'(\d{1,2}h\s*\d{0,2}m?)', html)
    valid_durations = []
    for d in durations:
        match = re.match(r'(\d+)h', d)
        if match and 10 <= int(match.group(1)) <= 50:
            valid_durations.append(d)

    sorted_prices = sorted(set(flight_prices))
    min_usd = int(sorted_prices[0] * rate) if sorted_prices else 0

    # Find shortest duration
    shortest = "N/A"
    if valid_durations:
        def duration_hours(d):
            m = re.match(r'(\d+)h\s*(\d*)', d)
            return int(m.group(1)) + int(m.group(2) or 0) / 60 if m else 99
        shortest = min(valid_durations, key=duration_hours)

    results = {
        "route": f"{origin} → {destination}",
        "date": date_str,
        "currency": currency,
        "currency_symbol": symbol,
        "usd_rate": rate,
        "prices": sorted_prices,
        "min_usd": min_usd,
        "airlines": list(found_airlines),
        "durations": list(set(valid_durations)),
        "shortest_duration": shortest,
        "scraped_at": datetime.now().isoformat()
    }

    # Save to file
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    return results


def load_results():
    """Load cached results if available."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return None


@app.route("/")
def index():
    results = load_results()
    default_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    return render_template_string(
        HTML_TEMPLATE,
        results=results,
        airports=AIRPORTS,
        default_date=default_date
    )


@app.route("/api/search")
def api_search():
    origin = request.args.get("origin", "SIN")
    destination = request.args.get("destination", "NYCA")
    date = request.args.get("date", "")

    if not date:
        return jsonify({"error": "Date is required"})

    try:
        results = scrape_flights(origin, destination, date)
        if results:
            return jsonify({"success": True, "results": results})
        else:
            return jsonify({"error": "Failed to fetch results"})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("FLIGHT PRICE DASHBOARD")
    print("=" * 50)
    print("\nStarting server at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
