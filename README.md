# TripVibe ✈️🍔

> **The McDonald's of Travel** - Build your trip like ordering a combo meal

A modern travel search platform that scrapes real flight and hotel data, presenting them as customizable bundles with Gen Z-friendly vibes.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-green)
![Scrapling](https://img.shields.io/badge/Scrapling-0.4+-purple)

## Features

### 🛫 TripVibe Flights (Port 5001)
- **Real-time Skyscanner scraping** - Live flight prices in SGD
- **Persona-based filtering** - Budget Backpacker, Digital Nomad, Bougie Traveler, etc.
- **Vibe filters** - "On a whim", "Need for speed", "Planet-friendly"
- **Client-side filtering** - Instant results, no page reload

### 🍔 TripVibe Bundles (Port 5002)
- **Dual scraping** - Skyscanner (flights) + Booking.com (hotels)
- **Bundle cards** - Flight + Hotel shown together like a combo meal
- **Swap modals** - Pick alternative flights/hotels
- **Add-ons** - Extra baggage, breakfast, airport transfer
- **Dynamic pricing** - Updates as you customize
- **Sort options** - Best Value, Cheapest, Fastest

## Quick Start

```bash
# Clone the repo
git clone https://github.com/kopi-koubou/tripvibe.git
cd tripvibe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for StealthyFetcher)
playwright install chromium

# Run TripVibe Bundles
python tripvibe_v2.py
# Open http://127.0.0.1:5002
```

## Apps

| App | Port | Description |
|-----|------|-------------|
| `dashboard.py` | 5000 | Simple flight search |
| `tripvibe.py` | 5001 | Vibe-based flight filters |
| `tripvibe_v2.py` | 5002 | Flight + Hotel bundles 🍔 |

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  User Input │────▶│  Scrapling   │────▶│  TripVibe   │
│  (Route,    │     │  (Stealth    │     │  (Bundle &  │
│   Dates)    │     │   Browser)   │     │   Display)  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │  Skyscanner │          │ Booking.com │
       │  (Flights)  │          │  (Hotels)   │
       └─────────────┘          └─────────────┘
```

## Scraping Notes

This project uses [Scrapling](https://github.com/D4Vinci/Scrapling) with `StealthyFetcher` to bypass anti-bot protection.

**Rate Limits (approximate):**
- Skyscanner: ~100-500 queries/day before detection
- Booking.com: ~100-300 queries/day
- For production use, consider official APIs (Amadeus, Skyscanner Affiliate)

## Screenshots

### Bundle View
```
┌────────────────────────────────────────────────────────────┐
│  🎲 Perfect for spontaneous travelers         🏆 BEST VALUE │
├────────────────────────────────────────────────────────────┤
│  ✈️ FLIGHT                    🏨 HOTEL · 3 nights          │
│  🇸🇬 Singapore Airlines       Park Lane New York           │
│  08:00 ───✈️─── 18:00        ⭐⭐⭐⭐ · 8.5 · City Center   │
│  S$745 · 18h · 1 stop        S$100/night                   │
├────────────────────────────────────────────────────────────┤
│  🔄 Swap flight    [+🧳 bag] [+🍽️ breakfast]    🔄 Swap hotel │
├────────────────────────────────────────────────────────────┤
│                    TOTAL: S$802                             │
│                    [Book This Bundle →]                     │
└────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend:** Flask, Python 3.9+
- **Scraping:** Scrapling (StealthyFetcher + Playwright)
- **Frontend:** Vanilla JS, CSS (no framework)
- **Data:** JSON file storage (for demo)

## Contributing

PRs welcome! Some ideas:
- [ ] Add more destinations
- [ ] Airbnb scraping
- [ ] Price alerts
- [ ] User accounts
- [ ] Trip sharing

## Disclaimer

This project is for **educational purposes only**. Scraping may violate terms of service of some websites. For production use, please use official APIs.

## License

MIT

---

Built with ☕ by [kopi-koubou](https://github.com/kopi-koubou)
