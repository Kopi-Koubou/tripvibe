"""
TripVibe - Next-Gen Travel Advisor
A personalized, vibe-based flight & hotel search for modern travelers.
"""

import json
import re
import random
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from scrapling import StealthyFetcher

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "tripvibe_data"
DATA_DIR.mkdir(exist_ok=True)

# Traveler Personas
PERSONAS = {
    "budget_backpacker": {
        "name": "Budget Backpacker",
        "emoji": "🎒",
        "description": "Maximum adventure, minimum spend",
        "priorities": ["cheapest", "flexible_dates", "hostels"],
        "vibe": "You're not here for luxury—you're here for the story."
    },
    "digital_nomad": {
        "name": "Digital Nomad",
        "emoji": "💻",
        "description": "Work from anywhere, live everywhere",
        "priorities": ["wifi", "long_layovers", "coworking"],
        "vibe": "Your office has the best views in the world."
    },
    "bougie_traveler": {
        "name": "Bougie Traveler",
        "emoji": "✨",
        "description": "Life's too short for budget airlines",
        "priorities": ["comfort", "lounge_access", "direct_flights"],
        "vibe": "Main character energy, premium seats only."
    },
    "family_planner": {
        "name": "Family Planner",
        "emoji": "👨‍👩‍👧‍👦",
        "description": "Keeping everyone happy (somehow)",
        "priorities": ["kid_friendly", "extra_luggage", "flexible"],
        "vibe": "Snacks packed, tablets charged, let's go!"
    },
    "eco_warrior": {
        "name": "Eco Warrior",
        "emoji": "🌱",
        "description": "Travel light on the planet",
        "priorities": ["low_carbon", "direct_flights", "sustainable"],
        "vibe": "Adventure shouldn't cost the Earth."
    },
    "spontaneous_soul": {
        "name": "Spontaneous Soul",
        "emoji": "🎲",
        "description": "Book now, figure it out later",
        "priorities": ["last_minute", "cheapest", "anywhere"],
        "vibe": "The best trips are the unplanned ones."
    }
}

# Vibe-based filters
VIBE_FILTERS = {
    "on_a_whim": {
        "label": "On a whim ✈️",
        "description": "Spontaneous getaway energy",
        "filter": lambda f: f.get("price", 9999) < 800,
        "tagline": "Life's too short for planning"
    },
    "need_speed": {
        "label": "Need for speed 🚀",
        "description": "Get there fastest",
        "filter": lambda f: f.get("duration_hours", 99) < 20,
        "tagline": "Time is money, bestie"
    },
    "extra_baggage": {
        "label": "Extra baggage 🧳",
        "description": "For the overpacker in you",
        "filter": lambda f: "Singapore Airlines" in f.get("airline", "") or "Emirates" in f.get("airline", ""),
        "tagline": "Yes, you need all 3 suitcases"
    },
    "eco_friendly": {
        "label": "Planet-friendly 🌍",
        "description": "Lowest carbon footprint",
        "filter": lambda f: f.get("stops", 9) <= 1,
        "tagline": "Less stops = less emissions"
    },
    "red_eye": {
        "label": "Red-eye warrior 🌙",
        "description": "Sleep on the plane, save on hotels",
        "filter": lambda f: True,  # Would filter by departure time
        "tagline": "Arrive at dawn, ready to explore"
    },
    "treat_yourself": {
        "label": "Treat yourself 💅",
        "description": "You deserve this",
        "filter": lambda f: f.get("price", 0) > 1500,
        "tagline": "Premium vibes only"
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TripVibe - Travel Your Way</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --gradient-4: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            --dark-bg: #0f0f1a;
            --card-bg: rgba(255,255,255,0.05);
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --accent: #667eea;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        .gradient-bg {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 600px;
            background: var(--gradient-1);
            opacity: 0.15;
            filter: blur(100px);
            z-index: -1;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            margin-bottom: 40px;
        }
        .logo {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2em;
            font-weight: 700;
            background: var(--gradient-3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .tagline {
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        /* Hero */
        .hero {
            text-align: center;
            padding: 60px 20px;
            margin-bottom: 40px;
        }
        .hero h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3.5em;
            margin-bottom: 20px;
            line-height: 1.1;
        }
        .hero h1 span {
            background: var(--gradient-2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero p {
            font-size: 1.3em;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
        }

        /* Search Box */
        .search-section {
            background: var(--card-bg);
            border-radius: 24px;
            padding: 40px;
            margin-bottom: 40px;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
        }
        .search-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr auto;
            gap: 20px;
            align-items: end;
        }
        .input-group { display: flex; flex-direction: column; gap: 8px; }
        .input-group label {
            font-size: 0.85em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .input-group input, .input-group select {
            padding: 16px 20px;
            border: 2px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            background: rgba(255,255,255,0.05);
            color: var(--text-primary);
            font-size: 1em;
            transition: all 0.3s;
        }
        .input-group input:focus, .input-group select:focus {
            outline: none;
            border-color: var(--accent);
            background: rgba(255,255,255,0.1);
        }
        .input-group select option { background: var(--dark-bg); }
        .search-btn {
            padding: 16px 40px;
            border: none;
            border-radius: 12px;
            background: var(--gradient-1);
            color: white;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            white-space: nowrap;
        }
        .search-btn:hover { transform: translateY(-2px); box-shadow: 0 20px 40px rgba(102,126,234,0.4); }
        .search-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        /* Persona Selector */
        .persona-section {
            margin-bottom: 40px;
        }
        .section-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.5em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .persona-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }
        .persona-card {
            background: var(--card-bg);
            border: 2px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
        }
        .persona-card:hover {
            border-color: var(--accent);
            transform: translateY(-4px);
        }
        .persona-card.active {
            border-color: var(--accent);
            background: rgba(102,126,234,0.2);
        }
        .persona-emoji { font-size: 2.5em; margin-bottom: 10px; }
        .persona-name { font-weight: 600; margin-bottom: 5px; }
        .persona-desc { font-size: 0.85em; color: var(--text-secondary); }

        /* Vibe Filters */
        .vibe-section { margin-bottom: 40px; }
        .vibe-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }
        .vibe-chip {
            padding: 12px 24px;
            border-radius: 50px;
            background: var(--card-bg);
            border: 2px solid rgba(255,255,255,0.1);
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.95em;
        }
        .vibe-chip:hover { border-color: var(--accent); }
        .vibe-chip.active {
            background: var(--gradient-1);
            border-color: transparent;
        }

        /* Results */
        .results-section { margin-bottom: 40px; }
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .results-count { color: var(--text-secondary); }
        .best-deal {
            background: var(--gradient-4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.5em;
            font-weight: 700;
        }

        .flight-card {
            background: var(--card-bg);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 16px;
            display: grid;
            grid-template-columns: 1fr 2fr 1fr 1fr;
            gap: 20px;
            align-items: center;
            transition: all 0.3s;
        }
        .flight-card:hover {
            border-color: var(--accent);
            transform: translateX(4px);
        }
        .flight-card.recommended {
            border: 2px solid;
            border-image: var(--gradient-4) 1;
            position: relative;
        }
        .flight-card.recommended::before {
            content: "✨ Perfect for you";
            position: absolute;
            top: -12px;
            left: 20px;
            background: var(--gradient-4);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            color: #0f0f1a;
        }
        .airline-info { display: flex; align-items: center; gap: 12px; }
        .airline-logo {
            width: 48px;
            height: 48px;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
        }
        .airline-name { font-weight: 600; }
        .airline-class { font-size: 0.85em; color: var(--text-secondary); }
        .flight-times {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .time-block { text-align: center; }
        .time { font-size: 1.4em; font-weight: 600; }
        .city { font-size: 0.85em; color: var(--text-secondary); }
        .flight-path {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 20px;
        }
        .path-line {
            flex: 1;
            height: 2px;
            background: rgba(255,255,255,0.2);
            position: relative;
        }
        .path-line::after {
            content: "✈️";
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
        }
        .duration {
            font-size: 0.85em;
            color: var(--text-secondary);
            text-align: center;
        }
        .stops {
            font-size: 0.8em;
            padding: 4px 12px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
        }
        .stops.direct { background: rgba(67,233,123,0.2); color: #43e97b; }
        .flight-meta { text-align: center; }
        .carbon {
            font-size: 0.8em;
            color: #43e97b;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }
        .price-block { text-align: right; }
        .price {
            font-size: 1.8em;
            font-weight: 700;
            background: var(--gradient-3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .price-note { font-size: 0.8em; color: var(--text-secondary); }
        .book-btn {
            margin-top: 10px;
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            background: var(--gradient-1);
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .book-btn:hover { transform: scale(1.05); }

        /* Loading */
        .loading {
            text-align: center;
            padding: 80px;
        }
        .loader {
            width: 60px;
            height: 60px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text {
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        .loading-subtext {
            color: var(--text-secondary);
            font-size: 0.9em;
        }

        /* Fun quotes */
        .travel-quote {
            text-align: center;
            padding: 40px;
            background: var(--card-bg);
            border-radius: 20px;
            margin-top: 40px;
        }
        .quote-text {
            font-size: 1.5em;
            font-style: italic;
            margin-bottom: 10px;
        }
        .quote-author { color: var(--text-secondary); }

        /* Responsive */
        @media (max-width: 1024px) {
            .search-grid { grid-template-columns: 1fr 1fr; }
            .flight-card { grid-template-columns: 1fr; text-align: center; }
            .flight-times { justify-content: center; }
            .price-block { text-align: center; }
        }
        @media (max-width: 768px) {
            .hero h1 { font-size: 2.5em; }
            .search-grid { grid-template-columns: 1fr; }
            .persona-grid { grid-template-columns: repeat(2, 1fr); }
        }

        /* Trending Section */
        .trending-section {
            margin-top: 60px;
            padding: 40px;
            background: var(--card-bg);
            border-radius: 24px;
        }
        .trend-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .trend-card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s;
        }
        .trend-card:hover { transform: translateY(-4px); }
        .trend-emoji { font-size: 2em; margin-bottom: 10px; }
        .trend-title { font-weight: 600; margin-bottom: 5px; }
        .trend-desc { font-size: 0.9em; color: var(--text-secondary); }
    </style>
</head>
<body>
    <div class="gradient-bg"></div>
    <div class="container">
        <header>
            <div>
                <div class="logo">TripVibe ✈️</div>
                <div class="tagline">Travel your way, not the boring way</div>
            </div>
        </header>

        <section class="hero">
            <h1>Find flights that match <span>your vibe</span></h1>
            <p>No more endless scrolling. Tell us how you travel, we'll find your perfect flight.</p>
        </section>

        <section class="search-section">
            <form id="searchForm" class="search-grid">
                <div class="input-group">
                    <label>From</label>
                    <select name="origin" id="origin">
                        <option value="SIN">🇸🇬 Singapore (SIN)</option>
                        <option value="NYCA">🇺🇸 New York (NYC)</option>
                        <option value="LHR">🇬🇧 London (LHR)</option>
                        <option value="NRT">🇯🇵 Tokyo (NRT)</option>
                        <option value="LAX">🇺🇸 Los Angeles (LAX)</option>
                        <option value="CDG">🇫🇷 Paris (CDG)</option>
                        <option value="DXB">🇦🇪 Dubai (DXB)</option>
                        <option value="BKK">🇹🇭 Bangkok (BKK)</option>
                        <option value="HKG">🇭🇰 Hong Kong (HKG)</option>
                        <option value="SYD">🇦🇺 Sydney (SYD)</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>To</label>
                    <select name="destination" id="destination">
                        <option value="NYCA">🇺🇸 New York (NYC)</option>
                        <option value="SIN">🇸🇬 Singapore (SIN)</option>
                        <option value="LHR">🇬🇧 London (LHR)</option>
                        <option value="NRT">🇯🇵 Tokyo (NRT)</option>
                        <option value="LAX">🇺🇸 Los Angeles (LAX)</option>
                        <option value="CDG">🇫🇷 Paris (CDG)</option>
                        <option value="DXB">🇦🇪 Dubai (DXB)</option>
                        <option value="BKK">🇹🇭 Bangkok (BKK)</option>
                        <option value="HKG">🇭🇰 Hong Kong (HKG)</option>
                        <option value="SYD">🇦🇺 Sydney (SYD)</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>When</label>
                    <input type="date" name="date" id="date" value="{{ default_date }}">
                </div>
                <div class="input-group">
                    <label>Travelers</label>
                    <select name="travelers">
                        <option value="1">1 traveler</option>
                        <option value="2">2 travelers</option>
                        <option value="3">3 travelers</option>
                        <option value="4">4+ travelers</option>
                    </select>
                </div>
                <button type="submit" class="search-btn" id="searchBtn">Find Flights ✨</button>
            </form>
        </section>

        <section class="persona-section">
            <h2 class="section-title">👤 What's your travel style?</h2>
            <div class="persona-grid">
                {% for key, persona in personas.items() %}
                <div class="persona-card" data-persona="{{ key }}">
                    <div class="persona-emoji">{{ persona.emoji }}</div>
                    <div class="persona-name">{{ persona.name }}</div>
                    <div class="persona-desc">{{ persona.description }}</div>
                </div>
                {% endfor %}
            </div>
        </section>

        <section class="vibe-section">
            <h2 class="section-title">🎯 Filter by vibe</h2>
            <div class="vibe-grid">
                {% for key, vibe in vibes.items() %}
                <div class="vibe-chip" data-vibe="{{ key }}">{{ vibe.label }}</div>
                {% endfor %}
            </div>
        </section>

        <section class="results-section" id="resultsSection">
            {% if results %}
            <div class="results-header">
                <div>
                    <h2 class="section-title">🛫 {{ results.flights|length }} flights found</h2>
                    <div class="results-count">{{ results.route }} · {{ results.date }}</div>
                </div>
                <div class="best-deal">From S${{ results.min_price }}</div>
            </div>

            {% for flight in results.flights[:10] %}
            <div class="flight-card {% if loop.index == 1 %}recommended{% endif %}">
                <div class="airline-info">
                    <div class="airline-logo">{{ flight.emoji }}</div>
                    <div>
                        <div class="airline-name">{{ flight.airline }}</div>
                        <div class="airline-class">Economy</div>
                    </div>
                </div>
                <div class="flight-times">
                    <div class="time-block">
                        <div class="time">{{ flight.depart }}</div>
                        <div class="city">{{ results.origin }}</div>
                    </div>
                    <div class="flight-path">
                        <div class="path-line"></div>
                    </div>
                    <div class="time-block">
                        <div class="time">{{ flight.arrive }}</div>
                        <div class="city">{{ results.destination }}</div>
                    </div>
                </div>
                <div class="flight-meta">
                    <div class="duration">{{ flight.duration }}</div>
                    <div class="stops {% if flight.stops == 0 %}direct{% endif %}">
                        {% if flight.stops == 0 %}Direct{% else %}{{ flight.stops }} stop{% if flight.stops > 1 %}s{% endif %}{% endif %}
                    </div>
                    <div class="carbon">🌱 {{ flight.carbon }}kg CO₂</div>
                </div>
                <div class="price-block">
                    <div class="price">S${{ flight.price }}</div>
                    <div class="price-note">per person</div>
                    <button class="book-btn">Select →</button>
                </div>
            </div>
            {% endfor %}
            {% else %}
            <div class="loading" id="placeholder">
                <div style="font-size: 4em; margin-bottom: 20px;">🌍</div>
                <div class="loading-text">Where to next?</div>
                <div class="loading-subtext">Select your route and hit search to find flights</div>
            </div>
            {% endif %}
        </section>

        <section class="trending-section">
            <h2 class="section-title">🔥 Trending right now</h2>
            <div class="trend-cards">
                <div class="trend-card">
                    <div class="trend-emoji">🗼</div>
                    <div class="trend-title">Tokyo is HOT</div>
                    <div class="trend-desc">Cherry blossom season bookings up 340%</div>
                </div>
                <div class="trend-card">
                    <div class="trend-emoji">🏝️</div>
                    <div class="trend-title">Bali bounce-back</div>
                    <div class="trend-desc">Digital nomad visas driving demand</div>
                </div>
                <div class="trend-card">
                    <div class="trend-emoji">🇵🇹</div>
                    <div class="trend-title">Lisbon vibes</div>
                    <div class="trend-desc">Europe's coolest city for remote work</div>
                </div>
                <div class="trend-card">
                    <div class="trend-emoji">🌙</div>
                    <div class="trend-title">Red-eye revival</div>
                    <div class="trend-desc">Night flights up 45% - save on hotels!</div>
                </div>
            </div>
        </section>

        <div class="travel-quote">
            <div class="quote-text">"The world is a book, and those who do not travel read only one page."</div>
            <div class="quote-author">— Saint Augustine (but like, still relevant)</div>
        </div>
    </div>

    <script>
        // Flight data from server
        const allFlights = {{ results.flights | tojson if results else '[]' }};
        const routeInfo = {{ {'route': results.route, 'origin': results.origin, 'destination': results.destination, 'date': results.date, 'min_price': results.min_price} | tojson if results else '{}' }};

        // Active filters
        let activeVibes = new Set();
        let activePersona = null;

        // Filter definitions (client-side)
        const vibeFilters = {
            'on_a_whim': f => f.price < 800,
            'need_speed': f => f.duration_hours < 20,
            'extra_baggage': f => f.airline.includes('Singapore') || f.airline.includes('Emirates'),
            'eco_friendly': f => f.stops <= 1,
            'red_eye': f => parseInt(f.depart.split(':')[0]) >= 20 || parseInt(f.depart.split(':')[0]) <= 6,
            'treat_yourself': f => f.price > 1200
        };

        // Persona filter mappings
        const personaFilters = {
            'budget_backpacker': f => f.price < 900,
            'digital_nomad': f => f.duration_hours > 15,  // Longer flights = more work time
            'bougie_traveler': f => f.airline.includes('Singapore') || f.airline.includes('Emirates') || f.airline.includes('Cathay'),
            'family_planner': f => f.stops <= 1,
            'eco_warrior': f => f.carbon < 1000,
            'spontaneous_soul': f => f.price < 850
        };

        function renderFlights(flights) {
            const section = document.getElementById('resultsSection');
            if (!flights.length) {
                section.innerHTML = `
                    <div class="loading">
                        <div style="font-size: 3em; margin-bottom: 20px;">😅</div>
                        <div class="loading-text">No flights match your vibe</div>
                        <div class="loading-subtext">Try removing some filters</div>
                    </div>
                `;
                return;
            }

            const minPrice = Math.min(...flights.map(f => f.price));

            let html = `
                <div class="results-header">
                    <div>
                        <h2 class="section-title">🛫 ${flights.length} flights found</h2>
                        <div class="results-count">${routeInfo.route} · ${routeInfo.date}</div>
                    </div>
                    <div class="best-deal">From S$${minPrice}</div>
                </div>
            `;

            flights.slice(0, 15).forEach((flight, idx) => {
                const isRecommended = idx === 0;
                html += `
                    <div class="flight-card ${isRecommended ? 'recommended' : ''}">
                        <div class="airline-info">
                            <div class="airline-logo">${flight.emoji}</div>
                            <div>
                                <div class="airline-name">${flight.airline}</div>
                                <div class="airline-class">Economy</div>
                            </div>
                        </div>
                        <div class="flight-times">
                            <div class="time-block">
                                <div class="time">${flight.depart}</div>
                                <div class="city">${routeInfo.origin}</div>
                            </div>
                            <div class="flight-path">
                                <div class="path-line"></div>
                            </div>
                            <div class="time-block">
                                <div class="time">${flight.arrive}</div>
                                <div class="city">${routeInfo.destination}</div>
                            </div>
                        </div>
                        <div class="flight-meta">
                            <div class="duration">${flight.duration}</div>
                            <div class="stops ${flight.stops === 0 ? 'direct' : ''}">
                                ${flight.stops === 0 ? 'Direct' : flight.stops + ' stop' + (flight.stops > 1 ? 's' : '')}
                            </div>
                            <div class="carbon">🌱 ${flight.carbon}kg CO₂</div>
                        </div>
                        <div class="price-block">
                            <div class="price">S$${flight.price.toLocaleString()}</div>
                            <div class="price-note">per person</div>
                            <button class="book-btn">Select →</button>
                        </div>
                    </div>
                `;
            });

            if (flights.length > 15) {
                html += `<p style="text-align: center; color: var(--text-secondary); margin-top: 20px;">+ ${flights.length - 15} more flights</p>`;
            }

            section.innerHTML = html;
        }

        function applyFilters() {
            let filtered = [...allFlights];

            // Apply vibe filters (OR logic - match any active vibe)
            if (activeVibes.size > 0) {
                filtered = filtered.filter(f => {
                    for (const vibe of activeVibes) {
                        if (vibeFilters[vibe] && vibeFilters[vibe](f)) return true;
                    }
                    return false;
                });
            }

            // Apply persona filter (if selected)
            if (activePersona && personaFilters[activePersona]) {
                filtered = filtered.filter(personaFilters[activePersona]);
            }

            // Sort by price
            filtered.sort((a, b) => a.price - b.price);

            renderFlights(filtered);

            // Update count display
            const countEl = document.querySelector('.results-count');
            if (countEl && activeVibes.size > 0) {
                countEl.textContent = `${routeInfo.route} · ${routeInfo.date} · Filtered`;
            }
        }

        // Persona selection
        document.querySelectorAll('.persona-card').forEach(card => {
            card.addEventListener('click', () => {
                const wasActive = card.classList.contains('active');
                document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('active'));

                if (wasActive) {
                    activePersona = null;
                } else {
                    card.classList.add('active');
                    activePersona = card.dataset.persona;
                }

                if (allFlights.length > 0) applyFilters();
            });
        });

        // Vibe filter selection
        document.querySelectorAll('.vibe-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const vibe = chip.dataset.vibe;

                if (chip.classList.contains('active')) {
                    chip.classList.remove('active');
                    activeVibes.delete(vibe);
                } else {
                    chip.classList.add('active');
                    activeVibes.add(vibe);
                }

                if (allFlights.length > 0) applyFilters();
            });
        });

        // Search form
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('searchBtn');
            const results = document.getElementById('resultsSection');

            btn.disabled = true;
            btn.textContent = 'Searching...';

            const loadingMessages = [
                "Finding your perfect flight...",
                "Scanning 18 airlines...",
                "Checking for secret deals...",
                "Almost there, bestie..."
            ];

            results.innerHTML = `
                <div class="loading">
                    <div class="loader"></div>
                    <div class="loading-text">${loadingMessages[0]}</div>
                    <div class="loading-subtext">This usually takes 10-15 seconds</div>
                </div>
            `;

            let msgIndex = 0;
            const msgInterval = setInterval(() => {
                msgIndex = (msgIndex + 1) % loadingMessages.length;
                const loadingText = results.querySelector('.loading-text');
                if (loadingText) loadingText.textContent = loadingMessages[msgIndex];
            }, 3000);

            const origin = document.getElementById('origin').value;
            const destination = document.getElementById('destination').value;
            const date = document.getElementById('date').value;

            try {
                const response = await fetch(`/api/search?origin=${origin}&destination=${destination}&date=${date}`);
                const data = await response.json();

                clearInterval(msgInterval);

                if (data.success) {
                    location.reload();
                } else {
                    results.innerHTML = `<div class="loading"><div class="loading-text">Oops! ${data.error}</div></div>`;
                }
            } catch (err) {
                clearInterval(msgInterval);
                results.innerHTML = `<div class="loading"><div class="loading-text">Something went wrong 😢</div></div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Find Flights ✨';
            }
        });
    </script>
</body>
</html>
"""

# Airline emoji mapping
AIRLINE_EMOJIS = {
    "Singapore Airlines": "🇸🇬",
    "Emirates": "🇦🇪",
    "Qatar Airways": "🇶🇦",
    "Cathay Pacific": "🇭🇰",
    "ANA": "🇯🇵",
    "All Nippon Airways": "🇯🇵",
    "JAL": "🇯🇵",
    "Japan Airlines": "🇯🇵",
    "Korean Air": "🇰🇷",
    "EVA Air": "🇹🇼",
    "China Airlines": "🇹🇼",
    "Air China": "🇨🇳",
    "United": "🇺🇸",
    "Delta": "🇺🇸",
    "American Airlines": "🇺🇸",
    "British Airways": "🇬🇧",
    "Lufthansa": "🇩🇪",
    "Turkish Airlines": "🇹🇷",
    "Asiana": "🇰🇷",
}


def scrape_flights(origin, destination, date_str):
    """Scrape flights and return structured data."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    sky_date = date_obj.strftime("%y%m%d")

    url = f"https://www.skyscanner.com.sg/transport/flights/{origin.lower()}/{destination.lower()}/{sky_date}/?currency=SGD&locale=en-GB&market=SG"

    fetcher = StealthyFetcher(headless=True)
    response = fetcher.fetch(url, solve_cloudflare=True)

    if response.status != 200:
        return None

    html = response.html_content

    # Extract prices
    prices = re.findall(r'\$\s*([\d,]+)', html)
    flight_prices = []
    for p in prices:
        try:
            val = int(p.replace(',', ''))
            if 400 <= val <= 20000:
                flight_prices.append(val)
        except:
            pass

    # Extract airlines
    airline_names = list(AIRLINE_EMOJIS.keys())
    found_airlines = set()
    for airline in airline_names:
        if airline.lower() in html.lower():
            found_airlines.add(airline)

    # Extract times
    times = list(set(re.findall(r'\b(\d{1,2}:\d{2})\b', html)))[:20]

    # Extract durations
    durations = re.findall(r'(\d{1,2}h\s*\d{0,2}m?)', html)
    valid_durations = []
    for d in durations:
        match = re.match(r'(\d+)h', d)
        if match and 10 <= int(match.group(1)) <= 50:
            valid_durations.append(d)

    # Build flight objects
    sorted_prices = sorted(set(flight_prices))
    airlines_list = list(found_airlines)

    flights = []
    for i, price in enumerate(sorted_prices[:20]):
        airline = airlines_list[i % len(airlines_list)] if airlines_list else "Unknown"
        duration = valid_durations[i % len(valid_durations)] if valid_durations else "20h"

        # Parse duration for carbon estimate
        dur_match = re.match(r'(\d+)h', duration)
        dur_hours = int(dur_match.group(1)) if dur_match else 20

        flights.append({
            "airline": airline,
            "emoji": AIRLINE_EMOJIS.get(airline, "✈️"),
            "price": price,
            "duration": duration,
            "duration_hours": dur_hours,
            "depart": times[i % len(times)] if times else "08:00",
            "arrive": times[(i + 5) % len(times)] if times else "18:00",
            "stops": 1 if dur_hours < 22 else (0 if dur_hours < 20 else 2),
            "carbon": int(dur_hours * 45),  # Rough estimate
        })

    results = {
        "route": f"{origin} → {destination}",
        "origin": origin,
        "destination": destination,
        "date": date_str,
        "flights": flights,
        "min_price": min(sorted_prices) if sorted_prices else 0,
        "airlines": airlines_list,
        "scraped_at": datetime.now().isoformat()
    }

    # Save
    with open(DATA_DIR / "latest_search.json", "w") as f:
        json.dump(results, f, indent=2)

    return results


def load_results():
    """Load cached results."""
    path = DATA_DIR / "latest_search.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


@app.route("/")
def index():
    results = load_results()
    default_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    return render_template_string(
        HTML_TEMPLATE,
        results=results,
        personas=PERSONAS,
        vibes=VIBE_FILTERS,
        default_date=default_date
    )


@app.route("/api/search")
def api_search():
    origin = request.args.get("origin", "SIN")
    destination = request.args.get("destination", "NYCA")
    date = request.args.get("date", "")

    if not date:
        return jsonify({"success": False, "error": "Date is required"})

    try:
        results = scrape_flights(origin, destination, date)
        if results:
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "No results found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   ✈️  TripVibe - Travel Your Way                           ║
║                                                            ║
║   Starting server at http://127.0.0.1:5001                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5001)
