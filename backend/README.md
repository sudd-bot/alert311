# Alert311 Backend

Automated 311 alerts via SMS for San Francisco.

## Overview

Users can sign up with a phone number and create alerts for specific 311 report types at specific addresses. When a matching report is filed, they receive an SMS notification.

## Architecture

- **FastAPI** backend with PostgreSQL database
- **Twilio Verification API** for phone number verification
- **Twilio SMS** for sending alerts
- **SF 311 API** (Spotmobile GraphQL) for fetching reports
- **Vercel Cron Jobs** for periodic polling (every 5 minutes)

## Database Schema

### Users
- `id`: Primary key
- `phone`: Verified phone number (E.164 format)
- `verified`: Boolean
- `account_type`: free/paid
- `verification_sid`: Twilio verification tracking

### Alerts
- `id`: Primary key
- `user_id`: Foreign key to users
- `address`: Street address
- `latitude`, `longitude`: Geocoded coordinates
- `report_type_id`: 311 ticket type UUID
- `report_type_name`: Human-readable name
- `active`: Boolean

### Reports
- `id`: Primary key
- `alert_id`: Foreign key to alerts
- `report_id`: 311 report UUID (unique)
- `report_data`: JSON (full 311 report data)
- `sms_sent`: Boolean

## API Endpoints

### Auth
- `POST /auth/register` - Register with phone, sends verification code
- `POST /auth/verify` - Verify phone with code
- `GET /auth/me?phone=+1...` - Get user info

### Alerts
- `POST /alerts?phone=+1...` - Create alert
- `GET /alerts?phone=+1...` - List user's alerts
- `GET /alerts/{id}?phone=+1...` - Get specific alert
- `PATCH /alerts/{id}?phone=+1...` - Update alert (activate/deactivate)
- `DELETE /alerts/{id}?phone=+1...` - Delete alert

### Reports
- `GET /reports?phone=+1...` - List all reports for user
- `GET /reports/{alert_id}?phone=+1...` - List reports for specific alert

### Cron (Protected by CRON_SECRET)
- `POST /cron/poll-reports` - Check 311 API for new matching reports
- `POST /cron/send-alerts` - Send SMS for pending reports

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`: From Twilio console
- `TWILIO_VERIFY_SERVICE_SID`: Create a Verify service in Twilio
- `TWILIO_FROM_NUMBER`: Your Twilio phone number
- `CRON_SECRET`: Random secret for cron job auth

### 3. Initialize Database

```bash
# Auto-creates tables on first startup
# For production, use Alembic migrations
uvicorn app.main:app --reload
```

### 4. Setup 311 API Tokens

The SF 311 API requires OAuth tokens. **Tokens are stored per-user** in the database.

**For each user:**

1. Run the token generator script:
   ```bash
   python scripts/get_311_tokens.py
   ```

2. Follow the browser OAuth flow

3. Copy the tokens and save them via API:
   ```bash
   curl -X POST 'http://localhost:8000/sf311/save-tokens?phone=+1234567890' \
     -H 'Content-Type: application/json' \
     -d '{
       "access_token": "...",
       "refresh_token": "...",
       "expires_in": 3600
     }'
   ```

Tokens are automatically refreshed by the system when they expire.

## Deployment (Vercel)

### 1. Create Postgres Database

Create a new Postgres database in Vercel (or use Supabase, Neon, etc.)

### 2. Set Environment Variables

In Vercel project settings, add all variables from `.env.example`

### 3. Deploy

```bash
vercel
```

### 4. Cron Jobs

Vercel will automatically set up cron jobs from `vercel.json`:
- `/cron/poll-reports` - Every 5 minutes
- `/cron/send-alerts` - Every 5 minutes

Make sure to set the `Authorization: Bearer {CRON_SECRET}` header.

## Development

Run locally:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs at: http://localhost:8000/docs

## TODO

- [ ] Implement full OAuth flow for 311 API
- [ ] Add JWT authentication instead of phone query param
- [ ] Add rate limiting
- [ ] Add subscription/payment integration
- [ ] Support multiple report types
- [ ] Add distance tolerance for address matching
- [ ] Add email alerts option
- [ ] Create admin dashboard
