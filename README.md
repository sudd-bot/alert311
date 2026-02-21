# Alert311

Get automated SMS alerts when specific 311 reports are filed in San Francisco.

**🌐 Live App:** [alert311-ui.vercel.app](https://alert311-ui.vercel.app)  
**🔌 API:** [backend-sigma-nine-42.vercel.app](https://backend-sigma-nine-42.vercel.app)

## Project Structure

```
alert311/
├── backend/        FastAPI backend + cron jobs (deployed to Vercel)
└── frontend/       Next.js frontend with Mapbox (deployed to Vercel)
```

## Features

- 📱 **SMS Verification** - Secure phone number verification via Twilio
- 🔔 **Custom Alerts** - Set alerts for specific addresses and report types
- 🗺️ **Interactive Map** - Mapbox-powered interface with dark theme
- 🤖 **Automated Polling** - Checks 311 API every 5 minutes
- 💬 **SMS Notifications** - Instant text alerts for matching reports
- 🎯 **Address Matching** - Geocoding with exact location targeting
- 🔒 **Security** - CORS protection, environment variable safety

## Current Status

✅ **Backend**: Deployed and operational
- FastAPI REST API running on Vercel serverless
- PostgreSQL database (Neon)
- Twilio integration (verification + SMS)
- SF 311 API integration active (system tokens with auto-refresh)
- Vercel Cron jobs for automated polling
- Database indexing for performance
- Comprehensive logging and monitoring

✅ **Frontend**: Deployed and operational
- Next.js app with Mapbox integration
- Phone verification flow
- Alert creation interface
- Modern dark theme with floating panels
- Responsive design (mobile + desktop)
- Real-time geocoding and map interaction

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

**Current Deployments:**
- **Frontend**: `alert311-ui.vercel.app` (manual deployment via Vercel CLI)
- **Backend**: `backend-sigma-nine-42.vercel.app` (manual deployment via Vercel CLI)
- **Database**: Neon Postgres (connected via `DATABASE_URL`)

**Deployment Process:**
The projects were deployed via Vercel CLI (not GitHub integration), so commits to GitHub do **not** auto-deploy. After making changes:

```bash
# Backend
cd backend
vercel --prod --yes

# Frontend  
cd ../frontend
vercel --prod --yes
```

**Planned:**
- Custom domain: `www.alert311.com` → frontend
- API domain: `api.alert311.com` → backend

### Environment Variables

**Backend (Vercel Project: backend):**
```
DATABASE_URL=postgresql://...
POSTGRES_URL=postgresql://...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_VERIFY_SERVICE_SID=...
TWILIO_FROM_NUMBER=+1...
CRON_SECRET=...
```

**Frontend (Vercel Project: alert311-ui):**
```
NEXT_PUBLIC_API_URL=https://backend-sigma-nine-42.vercel.app
NEXT_PUBLIC_MAPBOX_TOKEN=pk....
```

### Cron Jobs
Configured in `backend/vercel.json`:
- Poll 311 API every 5 minutes
- Send alert SMS every 5 minutes

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for PostgreSQL
- **Twilio** - SMS verification + alerts
- **Geopy** - Geocoding (OpenStreetMap/Nominatim)
- **httpx** - Async HTTP client for 311 API

### Frontend
- **Next.js** - React framework
- **Mapbox GL** - Interactive maps with dark theme
- **TailwindCSS** - Styling
- **react-map-gl** - React bindings for Mapbox

## API Documentation

Interactive docs available at:
- **Production**: https://backend-sigma-nine-42.vercel.app/docs
- **Local dev**: http://localhost:8000/docs

## Report Types

Available alert types in the app:
- **Parking on Sidewalk** (ID: `963f1454-7c22-43be-aacb-3f34ae5d0dc7`)
- **Graffiti**
- **Illegal Dumping**
- **Homeless Encampment**
- **Pothole**
- **Streetlight Out**

More types can be added by expanding `REPORT_TYPES` in the frontend `AlertPanel` component.

## Continuous Improvement

The project includes automated hourly health checks and incremental improvements via OpenClaw cron jobs. The system:
- Checks deployment status
- Reviews code for TODOs and potential improvements
- Makes safe, incremental updates
- Documents all changes in `STATUS.md`
- Messages the maintainer about important changes

See `STATUS.md` for detailed progress logs.

## Contributing

This is a work in progress. See `STATUS.md` for current state and known issues.

## License

MIT
