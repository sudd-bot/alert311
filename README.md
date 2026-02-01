# Alert311

Get automated SMS alerts when specific 311 reports are filed in San Francisco.

## Project Structure

```
alert311/
├── backend/        FastAPI backend + cron jobs
└── frontend/       Next.js frontend (coming soon)
```

## Features

- 📱 **SMS Verification** - Secure phone number verification via Twilio
- 🔔 **Custom Alerts** - Set alerts for specific addresses and report types
- 🤖 **Automated Polling** - Checks 311 API every 5 minutes
- 💬 **SMS Notifications** - Instant text alerts for matching reports
- 🗺️ **Address Matching** - Geocoding with exact address matching
- 💰 **Free & Paid Tiers** - Flexible account types (payment integration coming)

## Current Status

✅ **Backend**: Complete and ready to deploy
- FastAPI REST API
- PostgreSQL database
- Twilio integration (verification + SMS)
- SF 311 API integration
- Vercel Cron jobs for polling

🚧 **Frontend**: Coming next
- Next.js app with map interface
- User registration/login
- Alert management UI
- Report history viewer

## Quick Start (Backend)

See [backend/README.md](backend/README.md) for detailed setup instructions.

### 1. Install & Configure
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### 2. Set Up Twilio
Follow the [Twilio Setup Guide](TWILIO_SETUP.md) to:
- Create a Twilio account (free trial available)
- Get your Account SID, Auth Token, and Verify Service SID
- Get a phone number for sending SMS

### 3. Test & Run
```bash
# Test your Twilio setup
python scripts/test_twilio.py

# Run the server
uvicorn app.main:app --reload
```

## Deployment

Deploy to Vercel (backend + frontend):

1. Create Postgres database on Vercel
2. Set environment variables
3. Run `vercel` in project root
4. Cron jobs auto-configured from `vercel.json`

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for PostgreSQL
- **Twilio** - SMS verification + alerts
- **Geopy** - Geocoding (OpenStreetMap/Nominatim)
- **httpx** - Async HTTP client for 311 API

### Frontend (Coming)
- **Next.js** - React framework
- **Mapbox/Leaflet** - Interactive maps
- **TailwindCSS** - Styling

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Report Types (Initial)

Starting with one report type:
- **Parking on Sidewalk** (ID: `963f1454-7c22-43be-aacb-3f34ae5d0dc7`)

More types can be added by expanding the config.

## Contributing

This is a work in progress. Frontend coming soon!

## License

MIT
