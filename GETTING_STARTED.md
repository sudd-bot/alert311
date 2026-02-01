# Getting Started with Alert311

Quick reference for setting up and deploying Alert311.

## 🚀 Setup Checklist

### 1. Twilio Setup (~10 minutes)

Follow **[TWILIO_SETUP.md](TWILIO_SETUP.md)** to:

- [ ] Create Twilio account (free trial: $15 credit)
- [ ] Get Account SID + Auth Token
- [ ] Create Verify Service → Get Service SID
- [ ] Get a phone number
- [ ] Add credentials to `.env`
- [ ] Test with `python backend/scripts/test_twilio.py`

**What you'll add to `.env`:**
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+12345678901
```

### 2. Database Setup

#### Option A: Vercel Postgres (Recommended for production)

1. Go to Vercel Dashboard → Storage → Create → Postgres
2. Copy the `DATABASE_URL` from the `.env.local` tab
3. Add to Vercel environment variables

#### Option B: Local Postgres (Development)

```bash
# macOS with Homebrew
brew install postgresql
brew services start postgresql

# Create database
createdb alert311

# Add to .env
DATABASE_URL=postgresql://localhost/alert311
```

### 3. Other Environment Variables

Add these to your `.env`:

```bash
# Database
DATABASE_URL=postgresql://...

# Twilio (from step 1)
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_VERIFY_SERVICE_SID=VAxxxx
TWILIO_FROM_NUMBER=+1xxx

# Cron Secret (generate a random string)
CRON_SECRET=your_random_secret_here

# App
DEBUG=false
```

**Generate a random CRON_SECRET:**
```bash
openssl rand -hex 32
```

### 4. Test Locally

```bash
cd backend
pip install -r requirements.txt

# Test services
python scripts/test_services.py

# Run server
uvicorn app.main:app --reload

# Visit http://localhost:8000/docs for API docs
```

### 5. Deploy to Vercel

```bash
cd ~/workspace/sudd-bot/alert311
vercel
```

**In Vercel Dashboard:**
1. Go to Settings → Environment Variables
2. Add all variables from your `.env` file
3. Redeploy

**Cron jobs will auto-configure** from `vercel.json`:
- `/cron/poll-reports` - Every 5 minutes
- `/cron/send-alerts` - Every 5 minutes

## 🔑 Per-User 311 Tokens

Each user needs their own SF 311 API tokens.

### Getting tokens for a user:

1. **Run the token generator:**
   ```bash
   cd backend
   python scripts/get_311_tokens.py
   ```

2. **Complete OAuth in browser** (signs into SF 311)

3. **Copy the tokens** from terminal output

4. **Save via API:**
   ```bash
   curl -X POST 'https://your-api.vercel.app/sf311/save-tokens?phone=+1234567890' \
     -H 'Content-Type: application/json' \
     -d '{
       "access_token": "eyJhbGc...",
       "refresh_token": "...",
       "expires_in": 3600
     }'
   ```

**Tokens auto-refresh** when they expire!

## 📱 Testing the Flow

### 1. Register a user

```bash
curl -X POST 'http://localhost:8000/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{"phone": "+16464171584"}'
```

You'll receive an SMS with a verification code.

### 2. Verify phone

```bash
curl -X POST 'http://localhost:8000/auth/verify' \
  -H 'Content-Type: application/json' \
  -d '{"phone": "+16464171584", "code": "123456"}'
```

### 3. Add 311 tokens (see above)

### 4. Create an alert

```bash
curl -X POST 'http://localhost:8000/alerts?phone=+16464171584' \
  -H 'Content-Type: application/json' \
  -d '{
    "address": "123 Main St"
  }'
```

### 5. Trigger cron jobs manually (for testing)

```bash
# Check for new 311 reports
curl -X POST 'http://localhost:8000/cron/poll-reports' \
  -H 'Authorization: Bearer YOUR_CRON_SECRET'

# Send pending alerts
curl -X POST 'http://localhost:8000/cron/send-alerts' \
  -H 'Authorization: Bearer YOUR_CRON_SECRET'
```

## 📊 API Endpoints

Full docs at: `http://localhost:8000/docs`

**Auth:**
- `POST /auth/register` - Register phone
- `POST /auth/verify` - Verify code
- `GET /auth/me?phone=+1...` - Get user info

**311 Tokens:**
- `POST /sf311/save-tokens?phone=+1...` - Save tokens
- `GET /sf311/token-status?phone=+1...` - Check token status

**Alerts:**
- `POST /alerts?phone=+1...` - Create alert
- `GET /alerts?phone=+1...` - List alerts
- `PATCH /alerts/{id}?phone=+1...` - Update alert
- `DELETE /alerts/{id}?phone=+1...` - Delete alert

**Reports:**
- `GET /reports?phone=+1...` - List all reports
- `GET /reports/{alert_id}?phone=+1...` - List alert's reports

## 🐛 Troubleshooting

### Twilio errors
- Run `python backend/scripts/test_twilio.py`
- Check [TWILIO_SETUP.md](TWILIO_SETUP.md) troubleshooting section

### Database errors
- Make sure PostgreSQL is running
- Check `DATABASE_URL` format
- Try: `python backend/scripts/init_db.py`

### Geocoding fails
- Check internet connection (uses OpenStreetMap API)
- Try a different address format
- Make sure address includes "San Francisco"

### No 311 reports found
- Check user has valid 311 tokens: `GET /sf311/token-status`
- Verify address is in San Francisco
- Try the same search in the reporter script:
  ```bash
  cd ../reporter
  python get_reports.py --address "123 Main St" --limit 20
  ```

## 📚 Next: Frontend

Once the backend is working, build the Next.js frontend with:
- User registration/login UI
- Interactive map for selecting addresses
- Alert management dashboard
- Report history viewer

## 💡 Tips

- **Free tier limits**: Twilio trial has $15 credit (~1,900 SMS or 300 verifications)
- **Costs after trial**: ~$0.05 per verification + $0.0079 per SMS = ~$0.07/user/month
- **Security**: Never commit `.env` to git (it's in `.gitignore`)
- **Production**: Use Vercel environment variables, not `.env` files
- **Monitoring**: Check Vercel Functions logs for cron job output
- **Rate limits**: 311 API has no published limits, but be respectful (5min polling is fine)

---

**Questions?** Check the READMEs or dive into the code - it's well-commented!
