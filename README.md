# Smart Agriculture AI

> An AI-powered national agricultural platform built for Burundian farmers — disease detection, farm planning, weather intelligence, market prices, and community support in one place.

---

## Overview

Smart Agriculture AI is a web platform designed to modernize agriculture in Burundi by giving farmers access to tools that were previously only available to large agricultural organizations. The platform works on any Android phone with Google Chrome, supports three languages (French, Kirundi, English), and uses only free and open-source technologies with zero recurring API costs.

The platform was built as a portfolio project demonstrating how artificial intelligence can be applied to solve real problems in developing agricultural economies.

---

## Features

### AI Crop Disease Diagnosis
Upload a photo of a sick crop and receive an instant diagnosis powered by Google Gemini Vision AI. The system identifies diseases, calculates a health score out of 100, and provides specific treatment recommendations in the farmer's language.

### Weather Intelligence
Real-time weather data for any location in Burundi using GPS auto-detection. Shows temperature, humidity, rainfall forecast, and a farming risk assessment (low / medium / high) based on conditions favorable to fungal diseases.

### Farm Planning & GPS Mapping
Three methods to map a field:
- **Draw** — trace the boundary on a satellite map
- **GPS Walk** — walk around the field with the phone, boundary is recorded automatically
- **Manual** — enter field size directly

After mapping, the system calculates seed quantities, fertilizer requirements, expected yield, projected revenue, and profit based on the farmer's actual costs.

### 3-Season Burundi Crop Calendar
A crop calendar adapted to Burundi's three agricultural seasons (A, B, C) covering 11 crops with monthly activities, optimal conditions, and disease risk periods.

### AI Planting Advice
Combines current weather data, the crop calendar, and Gemini AI to give a personalized planting recommendation — plant now, wait, or do not plant — with soil preparation steps and local risk warnings.

### Market Prices
Verified agronomists and government officials post current crop prices by province. Farmers see price trends and can plan their sales accordingly. New prices trigger automatic notifications to farmers in the relevant province.

### Community Forum
A public forum where farmers post questions, share experiences, and receive answers from other farmers and verified agronomists. Posts are organized by category (diseases, weather, seeds, fertilizers, market, government programs). Post authors can mark the best answer as a solution.

### Direct Messaging
Farmers can send private messages to verified agronomists and government officials. A verification badge system managed by administrators identifies trusted professionals. Random farmer-to-farmer direct messaging is restricted to keep the professional channel meaningful.

### Voice Assistant
A full voice interface designed for farmers who cannot read or write. The farmer taps a microphone button, speaks a question in French or Kirundi, and the AI responds with a short spoken answer read aloud automatically. Includes six quick-action topic buttons (disease, weather, planting, fertilizer, harvest, market prices) so the farmer can get help without typing anything.

### In-App Notifications
Automatic alerts for:
- Disease outbreaks detected in the farmer's province
- Replies to forum posts
- New market prices in the farmer's province
- Government announcements sent to all farmers

### Government Farm Map
A dashboard for government and admin users showing all registered farms on a Leaflet map. GPS-mapped fields appear as precise green circle markers. Farms without GPS appear as amber square markers placed at the province centroid. Clicking any marker shows full farm details.

### Disease Library & Outbreak Map
A visual library of common crop diseases in Burundi with symptoms, causes, and treatments. A province-level outbreak map shows where diseases have been recently detected.

### Multi-language Support
The full interface is available in French, Kirundi, and English. Language preference is saved per user account and can be changed at any time.

### Light / Dark Theme
Users can switch between the default dark green theme and a light theme suited for outdoor use in bright sunlight. Theme preference is saved to the user profile.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · Flask · SQLAlchemy · SQLite |
| AI Vision | Google Gemini 2.5 Flash (free tier) |
| Weather | Open-Meteo API (free, no API key required) |
| Geocoding | Nominatim / OpenStreetMap (free) |
| Maps | Leaflet.js · Leaflet-Geoman · Turf.js (all MIT) |
| Frontend | HTML · CSS · Vanilla JavaScript |
| Fonts | DM Serif Display · DM Sans · DM Mono (Google Fonts) |
| Charts | Chart.js |
| Auth | Flask-Login |

All APIs used are free. There are no subscription costs or hidden fees.

---

## Supported Crops

Common Bean · Maize · Cassava · Arabica Coffee · Sweet Potato · Banana · Rice · Sorghum · Irish Potato · Tomato · Wheat

---

## User Roles

| Role | Access |
|---|---|
| Farmer | Diagnosis, farm planning, calendar, forum, voice assistant, market prices, notifications |
| Government | All farmer features + government farm map + post market prices + send announcements |
| Admin | Full access + user management + verify professional badges |

---

## Installation

**Requirements:** Python 3.11+, Git, a Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/smart-agriculture-ai.git
cd smart-agriculture-ai

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac

# Install dependencies
pip install -r requirements.txt

# Create your environment file
cp .env.example .env
# Open .env and add your Gemini API key

# Initialize the database and seed sample data
python app.py &
python seed_data.py

# Start the server
python app.py
```

Open `http://localhost:5000` in your browser.

**Default admin account:** `admin` / `admin123` — change this password immediately after first login.

---

## Environment Variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
```

Never commit the `.env` file. It is excluded by `.gitignore`.

---

## Project Structure

```
smart-agriculture-ai/
├── app.py                  # Main Flask application and all core routes
├── models.py               # Database models (SQLAlchemy)
├── analyzer.py             # Gemini AI vision analysis
├── weather.py              # Open-Meteo weather integration
├── crop_calendar.py        # Burundi 3-season crop calendar data
├── translations.py         # FR / RN / EN string translations
├── notifications.py        # In-app notification helpers
├── farm_routes.py          # Farm planning blueprint
├── community_routes.py     # Forum and direct messaging blueprint
├── features_routes.py      # Advice, notifications, market prices blueprint
├── seed_data.py            # Sample data for development
├── static/
│   ├── css/main.css        # Full design system (dark + light themes)
│   └── js/main.js          # Client-side interactions
└── templates/
    ├── base.html           # Base layout with navigation
    ├── voice.html          # Voice assistant page
    ├── landing.html        # Public landing page
    ├── farm/               # Farm planning templates
    ├── community/          # Forum and messaging templates
    ├── features/           # Advice, market, notifications templates
    └── admin/              # Admin dashboard templates
```

---

## Languages

The platform interface is available in:
- **French** (default)
- **Kirundi** (national language of Burundi)
- **English**

Voice recognition uses the Web Speech API built into Google Chrome on Android. Kirundi uses French speech recognition as the closest available match since Kirundi is not yet supported by the Web Speech API.

---

## Screenshots

*Coming soon*

---

## Author

Built by **Twalaly** — Systems and Network Administrator, Université Polytechnique de Gitega (USPG), Burundi.

A portfolio project demonstrating applied AI for civic and agricultural development in East Africa.

---

## License

This project is open source and available for educational and civic use.
