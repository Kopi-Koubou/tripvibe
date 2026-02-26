"""
TripVibe v2 - The McDonald's of Travel
Bundle flights + hotels like ordering a combo meal.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from scrapling import StealthyFetcher

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "tripvibe_data"
DATA_DIR.mkdir(exist_ok=True)

# City mappings
CITIES = {
    "SIN": {"name": "Singapore", "booking": "Singapore", "flag": "🇸🇬"},
    "NYCA": {"name": "New York", "booking": "New+York", "flag": "🇺🇸"},
    "LHR": {"name": "London", "booking": "London", "flag": "🇬🇧"},
    "NRT": {"name": "Tokyo", "booking": "Tokyo", "flag": "🇯🇵"},
    "CDG": {"name": "Paris", "booking": "Paris", "flag": "🇫🇷"},
    "BKK": {"name": "Bangkok", "booking": "Bangkok", "flag": "🇹🇭"},
    "DXB": {"name": "Dubai", "booking": "Dubai", "flag": "🇦🇪"},
    "LAX": {"name": "Los Angeles", "booking": "Los+Angeles", "flag": "🇺🇸"},
}

AIRLINE_EMOJIS = {
    "Singapore Airlines": "🇸🇬", "Emirates": "🇦🇪", "Qatar Airways": "🇶🇦",
    "Cathay Pacific": "🇭🇰", "ANA": "🇯🇵", "All Nippon Airways": "🇯🇵",
    "United": "🇺🇸", "Delta": "🇺🇸", "British Airways": "🇬🇧",
    "Lufthansa": "🇩🇪", "Turkish Airlines": "🇹🇷", "Korean Air": "🇰🇷",
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TripVibe - Build Your Trip</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --gradient-4: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            --gradient-gold: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
            --dark-bg: #0a0a12;
            --card-bg: rgba(255,255,255,0.03);
            --card-hover: rgba(255,255,255,0.08);
            --text-primary: #ffffff;
            --text-secondary: #8888a0;
            --accent: #667eea;
            --success: #43e97b;
            --warning: #ffd200;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
            min-height: 100vh;
        }
        .gradient-orb {
            position: fixed;
            width: 600px;
            height: 600px;
            border-radius: 50%;
            filter: blur(120px);
            opacity: 0.15;
            pointer-events: none;
        }
        .orb-1 { top: -200px; left: -200px; background: #667eea; }
        .orb-2 { bottom: -200px; right: -200px; background: #f5576c; }

        .container { max-width: 1400px; margin: 0 auto; padding: 20px; position: relative; z-index: 1; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0 40px;
        }
        .logo {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.8em;
            font-weight: 700;
            background: var(--gradient-3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .logo-badge {
            font-size: 0.5em;
            background: var(--gradient-gold);
            -webkit-background-clip: unset;
            -webkit-text-fill-color: unset;
            color: #000;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
        }

        /* Hero */
        .hero {
            text-align: center;
            padding: 40px 20px 60px;
        }
        .hero h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3em;
            margin-bottom: 16px;
            line-height: 1.1;
        }
        .hero h1 span { background: var(--gradient-2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero p { font-size: 1.2em; color: var(--text-secondary); max-width: 500px; margin: 0 auto; }

        /* Search */
        .search-section {
            background: var(--card-bg);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 40px;
        }
        .search-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr 1fr auto;
            gap: 16px;
            align-items: end;
        }
        .input-group label {
            display: block;
            font-size: 0.8em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        .input-group select, .input-group input {
            width: 100%;
            padding: 14px 16px;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
            color: var(--text-primary);
            font-size: 1em;
        }
        .input-group select option { background: var(--dark-bg); }
        .search-btn {
            padding: 14px 32px;
            border: none;
            border-radius: 10px;
            background: var(--gradient-1);
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            white-space: nowrap;
        }
        .search-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(102,126,234,0.4); }
        .search-btn:disabled { opacity: 0.5; }

        /* Meal Deal Banner */
        .meal-deal-banner {
            background: var(--gradient-gold);
            color: #000;
            padding: 16px 24px;
            border-radius: 16px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .meal-deal-banner h3 { font-size: 1.3em; display: flex; align-items: center; gap: 10px; }
        .meal-deal-banner p { opacity: 0.8; }

        /* Bundle Cards */
        .bundles-section { margin-bottom: 40px; }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .section-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.5em;
        }
        .view-toggle {
            display: flex;
            gap: 8px;
        }
        .toggle-btn {
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
        }
        .toggle-btn.active {
            background: var(--accent);
            border-color: var(--accent);
            color: white;
        }

        /* Bundle Card - The Meal Deal */
        .bundle-card {
            background: var(--card-bg);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            overflow: hidden;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        .bundle-card:hover {
            border-color: var(--accent);
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .bundle-card.best-value {
            border: 2px solid;
            border-image: var(--gradient-gold) 1;
        }
        .bundle-header {
            background: rgba(255,255,255,0.02);
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .bundle-tag {
            font-size: 0.8em;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
        }
        .bundle-tag.value { background: var(--gradient-gold); color: #000; }
        .bundle-tag.eco { background: rgba(67,233,123,0.2); color: var(--success); }
        .bundle-tag.fast { background: rgba(102,126,234,0.2); color: var(--accent); }

        .bundle-content {
            display: grid;
            grid-template-columns: 1fr 1fr 200px;
            gap: 0;
        }

        /* Flight Section */
        .bundle-flight, .bundle-hotel {
            padding: 24px;
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        .section-label {
            font-size: 0.75em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .flight-main {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 12px;
        }
        .airline-logo {
            width: 44px;
            height: 44px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3em;
        }
        .flight-route {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .time-city {
            text-align: center;
        }
        .time { font-size: 1.2em; font-weight: 600; }
        .city { font-size: 0.8em; color: var(--text-secondary); }
        .route-line {
            flex: 1;
            height: 2px;
            background: linear-gradient(90deg, var(--accent), transparent, var(--accent));
            position: relative;
        }
        .route-line::before {
            content: "✈️";
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.9em;
        }
        .flight-meta {
            display: flex;
            gap: 16px;
            font-size: 0.85em;
            color: var(--text-secondary);
        }
        .flight-meta span { display: flex; align-items: center; gap: 4px; }
        .flight-price {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--accent);
        }

        /* Hotel Section */
        .hotel-main {
            display: flex;
            gap: 16px;
            margin-bottom: 12px;
        }
        .hotel-image {
            width: 80px;
            height: 60px;
            background: linear-gradient(135deg, #2a2a3a, #1a1a2a);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
        }
        .hotel-info { flex: 1; }
        .hotel-name { font-weight: 600; margin-bottom: 4px; font-size: 0.95em; }
        .hotel-rating {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85em;
        }
        .stars { color: #ffd200; }
        .review-score {
            background: var(--success);
            color: #000;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.8em;
        }
        .hotel-meta {
            font-size: 0.85em;
            color: var(--text-secondary);
            margin-top: 8px;
        }
        .hotel-price {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--success);
        }

        /* Price Section */
        .bundle-price {
            padding: 24px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: rgba(255,255,255,0.02);
        }
        .total-label { font-size: 0.8em; color: var(--text-secondary); margin-bottom: 4px; }
        .total-price {
            font-size: 2.2em;
            font-weight: 700;
            background: var(--gradient-3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .per-person { font-size: 0.8em; color: var(--text-secondary); margin-bottom: 16px; }
        .savings {
            font-size: 0.85em;
            color: var(--success);
            margin-bottom: 16px;
        }
        .book-bundle-btn {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 10px;
            background: var(--gradient-1);
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .book-bundle-btn:hover { transform: scale(1.02); }

        /* Customize Bundle */
        .customize-row {
            background: rgba(255,255,255,0.02);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        .customize-btn {
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.2s;
        }
        .customize-btn:hover { border-color: var(--accent); color: var(--accent); }
        .add-ons {
            display: flex;
            gap: 8px;
        }
        .addon-chip {
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(255,255,255,0.05);
            font-size: 0.8em;
            cursor: pointer;
            transition: all 0.2s;
        }
        .addon-chip:hover { background: rgba(102,126,234,0.2); }
        .addon-chip.selected { background: var(--accent); color: white; }

        /* Loading */
        .loading {
            text-align: center;
            padding: 80px 20px;
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
        .loading-emoji { font-size: 3em; margin-bottom: 16px; animation: bounce 1s ease infinite; }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

        /* How it works */
        .how-it-works {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 40px;
            margin-top: 60px;
            text-align: center;
        }
        .steps {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 30px;
            margin-top: 30px;
        }
        .step { text-align: center; }
        .step-icon { font-size: 2.5em; margin-bottom: 12px; }
        .step-title { font-weight: 600; margin-bottom: 6px; }
        .step-desc { font-size: 0.9em; color: var(--text-secondary); }

        @media (max-width: 1024px) {
            .search-grid { grid-template-columns: 1fr 1fr; }
            .bundle-content { grid-template-columns: 1fr; }
            .bundle-flight, .bundle-hotel { border-right: none; border-bottom: 1px solid rgba(255,255,255,0.05); }
            .steps { grid-template-columns: 1fr 1fr; }
        }
        @media (max-width: 768px) {
            .hero h1 { font-size: 2em; }
            .search-grid { grid-template-columns: 1fr; }
            .meal-deal-banner { flex-direction: column; gap: 10px; text-align: center; }
            .steps { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="gradient-orb orb-1"></div>
    <div class="gradient-orb orb-2"></div>

    <div class="container">
        <header>
            <div class="logo">
                TripVibe <span class="logo-badge">BUNDLES</span>
            </div>
        </header>

        <section class="hero">
            <h1>Build your trip <span>like a combo meal</span> 🍔</h1>
            <p>Flight + Hotel bundled together. Pick your vibe, we'll handle the rest.</p>
        </section>

        <section class="search-section">
            <form id="searchForm" class="search-grid">
                <div class="input-group">
                    <label>From</label>
                    <select name="origin" id="origin">
                        {% for code, city in cities.items() %}
                        <option value="{{ code }}" {% if code == 'SIN' %}selected{% endif %}>{{ city.flag }} {{ city.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="input-group">
                    <label>To</label>
                    <select name="destination" id="destination">
                        {% for code, city in cities.items() %}
                        <option value="{{ code }}" {% if code == 'NYCA' %}selected{% endif %}>{{ city.flag }} {{ city.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="input-group">
                    <label>Check-in</label>
                    <input type="date" name="checkin" id="checkin" value="{{ default_checkin }}">
                </div>
                <div class="input-group">
                    <label>Check-out</label>
                    <input type="date" name="checkout" id="checkout" value="{{ default_checkout }}">
                </div>
                <div class="input-group">
                    <label>Travelers</label>
                    <select name="travelers" id="travelers">
                        <option value="1">1 person</option>
                        <option value="2" selected>2 people</option>
                        <option value="3">3 people</option>
                        <option value="4">4 people</option>
                    </select>
                </div>
                <button type="submit" class="search-btn" id="searchBtn">Build My Trip ✨</button>
            </form>
        </section>

        <div class="meal-deal-banner">
            <div>
                <h3>🍟 Combo Deal Active</h3>
                <p>Book flight + hotel together and save up to 15%</p>
            </div>
            <div style="font-size: 2em;">🎉</div>
        </div>

        <section class="bundles-section" id="bundlesSection">
            {% if bundles %}
            <div class="section-header">
                <h2 class="section-title">🎯 {{ bundles|length }} bundles for your trip</h2>
                <div class="view-toggle">
                    <button class="toggle-btn active">Best Value</button>
                    <button class="toggle-btn">Cheapest</button>
                    <button class="toggle-btn">Fastest</button>
                </div>
            </div>

            {% for bundle in bundles %}
            <div class="bundle-card {% if loop.index == 1 %}best-value{% endif %}">
                <div class="bundle-header">
                    <span>{{ bundle.vibe_text }}</span>
                    {% if loop.index == 1 %}
                    <span class="bundle-tag value">🏆 BEST VALUE</span>
                    {% elif bundle.flight.duration_hours < 20 %}
                    <span class="bundle-tag fast">⚡ FASTEST</span>
                    {% elif bundle.flight.carbon < 800 %}
                    <span class="bundle-tag eco">🌱 ECO-FRIENDLY</span>
                    {% endif %}
                </div>

                <div class="bundle-content">
                    <div class="bundle-flight">
                        <div class="section-label">✈️ FLIGHT</div>
                        <div class="flight-main">
                            <div class="airline-logo">{{ bundle.flight.emoji }}</div>
                            <div class="flight-route">
                                <div class="time-city">
                                    <div class="time">{{ bundle.flight.depart }}</div>
                                    <div class="city">{{ bundle.origin }}</div>
                                </div>
                                <div class="route-line"></div>
                                <div class="time-city">
                                    <div class="time">{{ bundle.flight.arrive }}</div>
                                    <div class="city">{{ bundle.destination }}</div>
                                </div>
                            </div>
                        </div>
                        <div class="flight-meta">
                            <span>{{ bundle.flight.airline }}</span>
                            <span>⏱️ {{ bundle.flight.duration }}</span>
                            <span>{{ bundle.flight.stops }} stop{% if bundle.flight.stops != 1 %}s{% endif %}</span>
                            <span class="flight-price">S${{ bundle.flight.price }}</span>
                        </div>
                    </div>

                    <div class="bundle-hotel">
                        <div class="section-label">🏨 HOTEL · {{ bundle.nights }} nights</div>
                        <div class="hotel-main">
                            <div class="hotel-image">🏨</div>
                            <div class="hotel-info">
                                <div class="hotel-name">{{ bundle.hotel.name }}</div>
                                <div class="hotel-rating">
                                    <span class="stars">{{ '⭐' * bundle.hotel.stars }}</span>
                                    <span class="review-score">{{ bundle.hotel.score }}</span>
                                    <span style="color: var(--text-secondary);">{{ bundle.hotel.reviews }} reviews</span>
                                </div>
                            </div>
                        </div>
                        <div class="hotel-meta">
                            <span>📍 {{ bundle.hotel.location }}</span> ·
                            <span class="hotel-price">S${{ bundle.hotel.price_per_night }}/night</span>
                        </div>
                    </div>

                    <div class="bundle-price">
                        <div class="total-label">TOTAL BUNDLE</div>
                        <div class="total-price">S${{ bundle.total_price }}</div>
                        <div class="per-person">per person</div>
                        {% if bundle.savings > 0 %}
                        <div class="savings">💰 Save S${{ bundle.savings }} vs booking separately</div>
                        {% endif %}
                        <button class="book-bundle-btn" onclick="bookBundle({{ loop.index0 }})">Book This Bundle →</button>
                    </div>
                </div>

                <div class="customize-row">
                    <button class="customize-btn" onclick="swapFlight({{ loop.index0 }})">🔄 Swap flight</button>
                    <div class="add-ons">
                        <span class="addon-chip" onclick="toggleAddon({{ loop.index0 }}, 'bag', this)">+ 🧳 Extra bag</span>
                        <span class="addon-chip" onclick="toggleAddon({{ loop.index0 }}, 'breakfast', this)">+ 🍽️ Breakfast</span>
                        <span class="addon-chip" onclick="toggleAddon({{ loop.index0 }}, 'transfer', this)">+ 🚗 Airport transfer</span>
                    </div>
                    <button class="customize-btn" onclick="swapHotel({{ loop.index0 }})">🔄 Swap hotel</button>
                </div>
            </div>
            {% endfor %}

            {% else %}
            <div class="loading" id="placeholder">
                <div class="loading-emoji">🌴</div>
                <h3 style="margin-bottom: 8px;">Ready to build your dream trip?</h3>
                <p style="color: var(--text-secondary);">Select your destination and dates above</p>
            </div>
            {% endif %}
        </section>

        <section class="how-it-works">
            <h2 class="section-title">How it works 🍔</h2>
            <p style="color: var(--text-secondary); margin-top: 8px;">Like ordering a combo meal, but for travel</p>
            <div class="steps">
                <div class="step">
                    <div class="step-icon">1️⃣</div>
                    <div class="step-title">Pick your destination</div>
                    <div class="step-desc">Where do you wanna go?</div>
                </div>
                <div class="step">
                    <div class="step-icon">2️⃣</div>
                    <div class="step-title">See instant bundles</div>
                    <div class="step-desc">We pair flights + hotels for you</div>
                </div>
                <div class="step">
                    <div class="step-icon">3️⃣</div>
                    <div class="step-title">Customize your combo</div>
                    <div class="step-desc">Swap, upgrade, add extras</div>
                </div>
                <div class="step">
                    <div class="step-icon">4️⃣</div>
                    <div class="step-title">Book & go</div>
                    <div class="step-desc">One checkout, done ✨</div>
                </div>
            </div>
        </section>
    </div>

    <!-- Modal Styles -->
    <style>
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
        }
        .modal-overlay.active { opacity: 1; visibility: visible; }
        .modal {
            background: var(--dark-bg);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            transform: scale(0.9);
            transition: transform 0.3s;
        }
        .modal-overlay.active .modal { transform: scale(1); }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .modal-title { font-size: 1.3em; font-weight: 600; }
        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5em;
            cursor: pointer;
        }
        .modal-close:hover { color: white; }
        .option-card {
            background: rgba(255,255,255,0.05);
            border: 2px solid transparent;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .option-card:hover { border-color: var(--accent); }
        .option-card.selected { border-color: var(--success); background: rgba(67,233,123,0.1); }
        .option-info { flex: 1; }
        .option-name { font-weight: 600; margin-bottom: 4px; }
        .option-meta { font-size: 0.85em; color: var(--text-secondary); }
        .option-price { font-size: 1.2em; font-weight: 600; color: var(--accent); }
        .modal-footer {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }
        .modal-btn {
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .modal-btn.secondary { background: transparent; border: 1px solid rgba(255,255,255,0.2); color: white; }
        .modal-btn.primary { background: var(--gradient-1); border: none; color: white; }
        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--success);
            color: #000;
            padding: 16px 32px;
            border-radius: 12px;
            font-weight: 600;
            z-index: 1001;
            transition: transform 0.3s;
        }
        .toast.show { transform: translateX(-50%) translateY(0); }
    </style>

    <!-- Modal HTML -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal">
            <div class="modal-header">
                <span class="modal-title" id="modalTitle">Select Option</span>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
            <div class="modal-footer">
                <button class="modal-btn secondary" onclick="closeModal()">Cancel</button>
                <button class="modal-btn primary" id="modalConfirm">Confirm</button>
            </div>
        </div>
    </div>

    <!-- Toast -->
    <div class="toast" id="toast">✅ Updated!</div>

    <script>
        // ========== DATA FROM SERVER ==========
        const allBundles = {{ bundles | tojson if bundles else '[]' }};
        const allFlights = {{ bundles[0].flight | tojson if bundles else '{}' }};
        const routeInfo = {
            origin: '{{ bundles[0].origin if bundles else "SIN" }}',
            destination: '{{ bundles[0].destination if bundles else "NYCA" }}',
            nights: {{ bundles[0].nights if bundles else 3 }}
        };

        // Alternative options (simulated from same scrape)
        const altFlights = allBundles.map(b => b.flight);
        const altHotels = allBundles.map(b => b.hotel);

        // Addon prices
        const addonPrices = {
            'bag': 50,
            'breakfast': 30,
            'transfer': 80
        };

        // Track selected addons per bundle
        const bundleAddons = {};
        allBundles.forEach((_, i) => bundleAddons[i] = new Set());

        // ========== MODAL FUNCTIONS ==========
        function openModal(title, content) {
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalBody').innerHTML = content;
            document.getElementById('modalOverlay').classList.add('active');
        }

        function closeModal() {
            document.getElementById('modalOverlay').classList.remove('active');
        }

        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);
        }

        // ========== SWAP FLIGHT ==========
        function swapFlight(bundleIndex) {
            let html = '<p style="color: var(--text-secondary); margin-bottom: 16px;">Choose a different flight:</p>';

            altFlights.forEach((flight, i) => {
                const isSelected = i === bundleIndex;
                html += `
                    <div class="option-card ${isSelected ? 'selected' : ''}" onclick="selectFlight(${bundleIndex}, ${i}, this)">
                        <div class="option-info">
                            <div class="option-name">${flight.emoji} ${flight.airline}</div>
                            <div class="option-meta">${flight.depart} → ${flight.arrive} · ${flight.duration} · ${flight.stops} stop${flight.stops !== 1 ? 's' : ''}</div>
                        </div>
                        <div class="option-price">S$${flight.price.toLocaleString()}</div>
                    </div>
                `;
            });

            openModal('✈️ Swap Flight', html);
            document.getElementById('modalConfirm').onclick = () => {
                closeModal();
                showToast('✈️ Flight updated!');
            };
        }

        function selectFlight(bundleIndex, flightIndex, el) {
            document.querySelectorAll('#modalBody .option-card').forEach(c => c.classList.remove('selected'));
            el.classList.add('selected');

            // Update the bundle card
            const newFlight = altFlights[flightIndex];
            const card = document.querySelectorAll('.bundle-card')[bundleIndex];
            if (card) {
                card.querySelector('.airline-logo').textContent = newFlight.emoji;
                card.querySelector('.flight-meta span:first-child').textContent = newFlight.airline;
                card.querySelector('.flight-price').textContent = `S$${newFlight.price}`;
                updateBundleTotal(bundleIndex, newFlight.price, null);
            }
        }

        // ========== SWAP HOTEL ==========
        function swapHotel(bundleIndex) {
            let html = '<p style="color: var(--text-secondary); margin-bottom: 16px;">Choose a different hotel:</p>';

            altHotels.forEach((hotel, i) => {
                const isSelected = i === bundleIndex;
                html += `
                    <div class="option-card ${isSelected ? 'selected' : ''}" onclick="selectHotel(${bundleIndex}, ${i}, this)">
                        <div class="option-info">
                            <div class="option-name">🏨 ${hotel.name}</div>
                            <div class="option-meta">${'⭐'.repeat(hotel.stars)} · ${hotel.score} · ${hotel.location}</div>
                        </div>
                        <div class="option-price">S$${hotel.price_total.toLocaleString()}</div>
                    </div>
                `;
            });

            openModal('🏨 Swap Hotel', html);
            document.getElementById('modalConfirm').onclick = () => {
                closeModal();
                showToast('🏨 Hotel updated!');
            };
        }

        function selectHotel(bundleIndex, hotelIndex, el) {
            document.querySelectorAll('#modalBody .option-card').forEach(c => c.classList.remove('selected'));
            el.classList.add('selected');

            // Update the bundle card
            const newHotel = altHotels[hotelIndex];
            const card = document.querySelectorAll('.bundle-card')[bundleIndex];
            if (card) {
                card.querySelector('.hotel-name').textContent = newHotel.name;
                card.querySelector('.hotel-price').textContent = `S$${newHotel.price_per_night}/night`;
                updateBundleTotal(bundleIndex, null, newHotel.price_total);
            }
        }

        // ========== UPDATE BUNDLE TOTAL ==========
        function updateBundleTotal(bundleIndex, newFlightPrice, newHotelPrice) {
            const bundle = allBundles[bundleIndex];
            const card = document.querySelectorAll('.bundle-card')[bundleIndex];
            if (!card || !bundle) return;

            const flightPrice = newFlightPrice !== null ? newFlightPrice : bundle.flight.price;
            const hotelPrice = newHotelPrice !== null ? newHotelPrice : bundle.hotel.price_total;

            // Add addons
            let addonTotal = 0;
            bundleAddons[bundleIndex].forEach(addon => {
                addonTotal += addonPrices[addon] || 0;
            });

            const total = Math.round((flightPrice + hotelPrice + addonTotal) * 0.92); // 8% bundle discount
            card.querySelector('.total-price').textContent = `S$${total.toLocaleString()}`;
        }

        // ========== ADDON TOGGLE ==========
        function toggleAddon(bundleIndex, addonType, el) {
            if (bundleAddons[bundleIndex].has(addonType)) {
                bundleAddons[bundleIndex].delete(addonType);
                el.classList.remove('selected');
            } else {
                bundleAddons[bundleIndex].add(addonType);
                el.classList.add('selected');
            }
            updateBundleTotal(bundleIndex, null, null);
            showToast(el.classList.contains('selected') ? `➕ Added ${addonType}` : `➖ Removed ${addonType}`);
        }

        // ========== BOOK BUNDLE ==========
        function bookBundle(bundleIndex) {
            const bundle = allBundles[bundleIndex];
            const addons = Array.from(bundleAddons[bundleIndex]);

            let html = `
                <div style="text-align: center; padding: 20px 0;">
                    <div style="font-size: 3em; margin-bottom: 16px;">🎉</div>
                    <h3 style="margin-bottom: 8px;">Booking Confirmed!</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 24px;">Well, not really—this is a demo 😅</p>

                    <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; text-align: left;">
                        <p style="margin-bottom: 12px;"><strong>✈️ Flight:</strong> ${bundle.flight.airline}</p>
                        <p style="margin-bottom: 12px;"><strong>🏨 Hotel:</strong> ${bundle.hotel.name}</p>
                        <p style="margin-bottom: 12px;"><strong>📅 Dates:</strong> ${routeInfo.nights} nights</p>
                        ${addons.length ? `<p style="margin-bottom: 12px;"><strong>➕ Add-ons:</strong> ${addons.join(', ')}</p>` : ''}
                        <p style="font-size: 1.3em; margin-top: 16px;"><strong>💰 Total: S$${bundle.total_price.toLocaleString()}</strong></p>
                    </div>

                    <p style="color: var(--text-secondary); margin-top: 20px; font-size: 0.9em;">
                        In a real app, this would redirect to Skyscanner + Booking.com
                    </p>
                </div>
            `;

            openModal('🎫 Your Trip', html);
            document.getElementById('modalConfirm').textContent = 'Close';
            document.getElementById('modalConfirm').onclick = closeModal;
        }

        // ========== SORT BUNDLES ==========
        function sortBundles(sortType) {
            const section = document.getElementById('bundlesSection');
            const cards = Array.from(document.querySelectorAll('.bundle-card'));

            let sorted;
            if (sortType === 'cheapest') {
                sorted = [...allBundles].sort((a, b) => a.total_price - b.total_price);
            } else if (sortType === 'fastest') {
                sorted = [...allBundles].sort((a, b) => a.flight.duration_hours - b.flight.duration_hours);
            } else {
                // Best value: price per hotel rating
                sorted = [...allBundles].sort((a, b) =>
                    (a.total_price / parseFloat(a.hotel.score)) - (b.total_price / parseFloat(b.hotel.score))
                );
            }

            // Re-render bundles
            showToast(`Sorted by ${sortType}`);
        }

        // ========== SEARCH FORM ==========
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('searchBtn');
            const section = document.getElementById('bundlesSection');

            btn.disabled = true;
            btn.textContent = 'Building...';

            const messages = [
                "Finding flights... ✈️",
                "Scanning hotels... 🏨",
                "Matching best combos... 🎯",
                "Calculating savings... 💰"
            ];

            section.innerHTML = `
                <div class="loading">
                    <div class="loader"></div>
                    <p style="font-size: 1.2em" id="loadingMsg">${messages[0]}</p>
                    <p style="color: var(--text-secondary); margin-top: 8px;">This takes about 20 seconds (scraping real data!)</p>
                </div>
            `;

            let i = 0;
            const msgInterval = setInterval(() => {
                i = (i + 1) % messages.length;
                const el = document.getElementById('loadingMsg');
                if (el) el.textContent = messages[i];
            }, 4000);

            const params = new URLSearchParams({
                origin: document.getElementById('origin').value,
                destination: document.getElementById('destination').value,
                checkin: document.getElementById('checkin').value,
                checkout: document.getElementById('checkout').value,
                travelers: document.getElementById('travelers').value
            });

            try {
                const res = await fetch('/api/bundle?' + params);
                const data = await res.json();
                clearInterval(msgInterval);

                if (data.success) {
                    location.reload();
                } else {
                    section.innerHTML = `<div class="loading"><p>😅 ${data.error}</p></div>`;
                }
            } catch (err) {
                clearInterval(msgInterval);
                section.innerHTML = `<div class="loading"><p>😅 Something went wrong</p></div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Build My Trip ✨';
            }
        });

        // ========== TOGGLE BUTTONS ==========
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const sortType = btn.textContent.toLowerCase().includes('cheap') ? 'cheapest' :
                                 btn.textContent.toLowerCase().includes('fast') ? 'fastest' : 'value';
                sortBundles(sortType);
            });
        });

        // Close modal on overlay click
        document.getElementById('modalOverlay').addEventListener('click', (e) => {
            if (e.target.id === 'modalOverlay') closeModal();
        });

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
    </script>
</body>
</html>
"""

VIBE_TEXTS = [
    "Perfect for spontaneous travelers 🎲",
    "Best bang for your buck 💰",
    "Ideal for the comfort-seeker ✨",
    "Great for first-timers 🌟",
    "Solid all-rounder pick 👍",
    "Budget-friendly gem 💎",
    "Popular with solo travelers 🎒",
    "Top-rated combo 🏆",
]


def scrape_flights(origin, destination, date_str):
    """Scrape flights from Skyscanner."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    sky_date = date_obj.strftime("%y%m%d")

    url = f"https://www.skyscanner.com.sg/transport/flights/{origin.lower()}/{destination.lower()}/{sky_date}/?currency=SGD"

    fetcher = StealthyFetcher(headless=True)
    response = fetcher.fetch(url, solve_cloudflare=True)

    if response.status != 200:
        return []

    html = response.html_content

    # Extract prices
    prices = re.findall(r'\$\s*([\d,]+)', html)
    flight_prices = []
    for p in prices:
        try:
            val = int(p.replace(',', ''))
            if 400 <= val <= 15000:
                flight_prices.append(val)
        except:
            pass

    # Airlines
    airline_names = list(AIRLINE_EMOJIS.keys())
    found_airlines = [a for a in airline_names if a.lower() in html.lower()]

    # Times
    times = list(set(re.findall(r'\b(\d{1,2}:\d{2})\b', html)))[:20]

    # Durations
    durations = re.findall(r'(\d{1,2}h\s*\d{0,2}m?)', html)
    valid_durations = [d for d in durations if re.match(r'(\d+)h', d) and 10 <= int(re.match(r'(\d+)h', d).group(1)) <= 50]

    sorted_prices = sorted(set(flight_prices))
    flights = []

    for i, price in enumerate(sorted_prices[:10]):
        airline = found_airlines[i % len(found_airlines)] if found_airlines else "Unknown"
        duration = valid_durations[i % len(valid_durations)] if valid_durations else "20h"
        dur_match = re.match(r'(\d+)h', duration)
        dur_hours = int(dur_match.group(1)) if dur_match else 20

        flights.append({
            "airline": airline,
            "emoji": AIRLINE_EMOJIS.get(airline, "✈️"),
            "price": price,
            "duration": duration,
            "duration_hours": dur_hours,
            "depart": times[i % len(times)] if times else "08:00",
            "arrive": times[(i + 3) % len(times)] if times else "18:00",
            "stops": 1 if dur_hours < 22 else 2,
            "carbon": int(dur_hours * 45),
        })

    return flights


def scrape_hotels(city, checkin, checkout):
    """Scrape hotels from Booking.com."""
    city_info = CITIES.get(city, {"booking": city})
    booking_city = city_info.get("booking", city)

    url = f"https://www.booking.com/searchresults.html?ss={booking_city}&checkin={checkin}&checkout={checkout}&group_adults=2&no_rooms=1&selected_currency=SGD"

    fetcher = StealthyFetcher(headless=True)
    response = fetcher.fetch(url, solve_cloudflare=True)

    if response.status != 200:
        return []

    html = response.html_content

    # Extract hotel names
    name_pattern = r'data-testid="title"[^>]*>([^<]+)<'
    names = re.findall(name_pattern, html)[:15]

    # Extract prices (SGD)
    price_pattern = r'SGD\s*([\d,]+)|S\$\s*([\d,]+)|\$\s*([\d,]+)'
    price_matches = re.findall(price_pattern, html)
    prices = []
    for match in price_matches:
        p = match[0] or match[1] or match[2]
        try:
            val = int(p.replace(',', ''))
            if 50 <= val <= 5000:
                prices.append(val)
        except:
            pass

    # Extract scores
    scores = re.findall(r'(\d\.\d)\s*(?:Superb|Excellent|Very Good|Good|Pleasant)', html)

    hotels = []
    locations = ["City Center", "Downtown", "Near Airport", "Business District", "Waterfront", "Arts District"]

    for i in range(min(8, len(names), len(prices))):
        nights = (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days
        total_price = prices[i] if i < len(prices) else 150 * nights

        hotels.append({
            "name": names[i][:35] + "..." if len(names[i]) > 35 else names[i],
            "price_total": total_price,
            "price_per_night": total_price // nights if nights > 0 else total_price,
            "stars": min(5, 3 + (i % 3)),
            "score": scores[i] if i < len(scores) else f"{8.0 + (i % 15) / 10:.1f}",
            "reviews": 500 + (i * 234) % 2000,
            "location": locations[i % len(locations)],
        })

    return hotels


def create_bundles(flights, hotels, origin, destination, nights):
    """Create flight + hotel bundles."""
    bundles = []

    for i, flight in enumerate(flights[:6]):
        hotel = hotels[i % len(hotels)] if hotels else {
            "name": "City Hotel",
            "price_total": 200 * nights,
            "price_per_night": 200,
            "stars": 4,
            "score": "8.5",
            "reviews": 1000,
            "location": "City Center"
        }

        flight_price = flight["price"]
        hotel_price = hotel["price_total"]

        # Bundle discount (5-15%)
        discount_pct = 0.05 + (i * 0.02)
        separate_total = flight_price + hotel_price
        bundle_total = int(separate_total * (1 - discount_pct))
        savings = separate_total - bundle_total

        bundles.append({
            "flight": flight,
            "hotel": hotel,
            "origin": origin,
            "destination": destination,
            "nights": nights,
            "total_price": bundle_total,
            "savings": savings,
            "vibe_text": VIBE_TEXTS[i % len(VIBE_TEXTS)],
        })

    # Sort by value (price per quality)
    bundles.sort(key=lambda b: b["total_price"] / (float(b["hotel"]["score"]) + 0.1))

    return bundles


def load_bundles():
    """Load cached bundles."""
    path = DATA_DIR / "bundles.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


@app.route("/")
def index():
    bundles_data = load_bundles()
    default_checkin = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    default_checkout = (datetime.now() + timedelta(days=93)).strftime("%Y-%m-%d")

    return render_template_string(
        HTML_TEMPLATE,
        bundles=bundles_data.get("bundles") if bundles_data else None,
        cities=CITIES,
        default_checkin=default_checkin,
        default_checkout=default_checkout,
    )


@app.route("/api/bundle")
def api_bundle():
    origin = request.args.get("origin", "SIN")
    destination = request.args.get("destination", "NYCA")
    checkin = request.args.get("checkin")
    checkout = request.args.get("checkout")

    if not checkin or not checkout:
        return jsonify({"success": False, "error": "Dates required"})

    try:
        nights = (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days
        if nights <= 0:
            return jsonify({"success": False, "error": "Invalid dates"})

        # Scrape flights
        flights = scrape_flights(origin, destination, checkin)
        if not flights:
            return jsonify({"success": False, "error": "No flights found"})

        # Scrape hotels
        dest_city = CITIES.get(destination, {}).get("name", destination)
        hotels = scrape_hotels(destination, checkin, checkout)

        # Create bundles
        bundles = create_bundles(flights, hotels, origin, destination, nights)

        # Save
        data = {
            "bundles": bundles,
            "origin": origin,
            "destination": destination,
            "checkin": checkin,
            "checkout": checkout,
            "scraped_at": datetime.now().isoformat()
        }

        with open(DATA_DIR / "bundles.json", "w") as f:
            json.dump(data, f, indent=2)

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🍔 TripVibe BUNDLES - The McDonald's of Travel              ║
║                                                               ║
║   Server: http://127.0.0.1:5002                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5002)
