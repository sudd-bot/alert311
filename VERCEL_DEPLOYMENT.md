# Vercel Deployment Guide

## Step 1: Create Vercel Account & Install CLI

If you haven't already:

1. Go to https://vercel.com/signup
2. Sign up with GitHub (easiest)
3. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

## Step 2: Create Postgres Database

1. Go to https://vercel.com/dashboard
2. Click **Storage** in the top nav
3. Click **Create Database**
4. Choose **Postgres**
5. Name it: `alert311-db`
6. Region: Choose closest to you (e.g., `US East`)
7. Click **Create**

**Save this for later:**
- After creation, click on your database
- Go to the **`.env.local`** tab
- Copy the `POSTGRES_URL` value (starts with `postgres://...`)

## Step 3: Link Project to Vercel

In your terminal:

```bash
cd ~/workspace/sudd-bot/alert311
vercel
```

**Answer the prompts:**
- `Set up and deploy "~/workspace/sudd-bot/alert311"?` → **Y**
- `Which scope?` → Choose your account
- `Link to existing project?` → **N**
- `What's your project's name?` → **alert311**
- `In which directory is your code located?` → **backend**
- `Want to override the settings?` → **N**

Vercel will deploy, but it will fail initially (missing environment variables). That's okay!

## Step 4: Link Database to Project

1. Go to https://vercel.com/dashboard
2. Click on your **alert311** project
3. Go to **Storage** tab
4. Click **Connect Store**
5. Select your **alert311-db** Postgres database
6. Click **Connect**

This automatically adds the `POSTGRES_URL` environment variable!

## Step 5: Add Environment Variables

Still in your Vercel project settings:

1. Go to **Settings** → **Environment Variables**
2. Add each of these (one by one):

**Twilio Variables:**
```
TWILIO_ACCOUNT_SID = ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN = your_auth_token_here
TWILIO_VERIFY_SERVICE_SID = VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER = +1234567890
```

*Use your actual Twilio credentials from the `.env` file*

**SF 311 API (defaults - already set in code, but add for clarity):**
```
SF311_BASE_URL = https://mobile311.sfgov.org
SF311_CLIENT_ID = KLHhIUu56qWPHrYA16MUvxBXaJbPoAmKDbFjDFhe
SF311_REDIRECT_URI = sf311://auth
SF311_SCOPE = refresh_token read write openid
SF311_GRAPHQL_URL = https://mobile311.sfgov.org/api/graphql
```

**Report Types:**
```
DEFAULT_REPORT_TYPE_ID = 963f1454-7c22-43be-aacb-3f34ae5d0dc7
DEFAULT_REPORT_TYPE_NAME = Parking on Sidewalk
```

**Cron Secret** (generate a random one):
```bash
# Run this locally to generate:
openssl rand -hex 32
```
Then add:
```
CRON_SECRET = <paste the generated secret here>
```

**App Settings:**
```
DEBUG = false
```

**Important:** For each variable:
- Click **Add Another**
- Enter **Name** and **Value**
- Select environments: **Production**, **Preview**, **Development** (all three)
- Click **Save**

## Step 6: Configure Build Settings

Vercel should auto-detect Python, but let's make sure:

1. Go to **Settings** → **General**
2. Scroll to **Build & Development Settings**
3. Verify:
   - **Framework Preset**: Other
   - **Root Directory**: `backend`
   - **Build Command**: (leave empty, Vercel auto-detects)
   - **Output Directory**: (leave empty)
   - **Install Command**: `pip install -r requirements.txt`

4. Click **Save** if you made changes

## Step 7: Fix Vercel Configuration

We need to update the `vercel.json` to work with Vercel's Python runtime:

**The issue:** Vercel needs specific configuration for FastAPI.

I'll create a new `vercel.json` for you now...

## Step 8: Redeploy

After the vercel.json is updated and pushed:

```bash
cd ~/workspace/sudd-bot/alert311
git add .
git commit -m "Update vercel.json for Python deployment"
git push origin main
```

Then in Vercel dashboard:
1. Go to your **alert311** project
2. Click **Deployments**
3. Click **Redeploy** on the latest deployment

Or from CLI:
```bash
vercel --prod
```

## Step 9: Verify Deployment

Once deployed, you should see:

1. **Deployment URL**: Something like `https://alert311-xxx.vercel.app`
2. Test the health endpoint:
   ```bash
   curl https://alert311-xxx.vercel.app/health
   ```
   Should return: `{"status":"healthy"}`

3. Check API docs:
   ```
   https://alert311-xxx.vercel.app/docs
   ```

## Step 10: Set Up Cron Jobs

Vercel cron jobs should auto-configure from `vercel.json`, but let's verify:

1. In Vercel project → **Settings** → **Cron Jobs**
2. You should see:
   - `/cron/poll-reports` - Every 5 minutes (`*/5 * * * *`)
   - `/cron/send-alerts` - Every 5 minutes (`*/5 * * * *`)

If not showing, the deployment might have failed. Check logs.

**Important:** Cron jobs need authentication!

The cron endpoints expect a header:
```
Authorization: Bearer <your-CRON_SECRET>
```

Vercel cron automatically adds this header using the `CRON_SECRET` env var.

## Step 11: Test End-to-End

Now test the full flow:

### 1. Register a phone number
```bash
curl -X POST 'https://alert311-xxx.vercel.app/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{"phone": "+16464171584"}'
```

You should receive an SMS verification code!

### 2. Verify the code
```bash
curl -X POST 'https://alert311-xxx.vercel.app/auth/verify' \
  -H 'Content-Type: application/json' \
  -d '{"phone": "+16464171584", "code": "123456"}'
```

### 3. Get 311 tokens (see GETTING_STARTED.md)

### 4. Create an alert
```bash
curl -X POST 'https://alert311-xxx.vercel.app/alerts?phone=+16464171584' \
  -H 'Content-Type: application/json' \
  -d '{"address": "123 Main St"}'
```

### 5. Wait for cron jobs to run (every 5 min)
- Or manually trigger (for testing):
  ```bash
  curl -X POST 'https://alert311-xxx.vercel.app/cron/poll-reports' \
    -H 'Authorization: Bearer YOUR_CRON_SECRET'
  ```

## Troubleshooting

### Build fails
- Check **Deployments** → Click deployment → View **Build Logs**
- Common issue: Missing dependencies in `requirements.txt`
- Fix: Update requirements, commit, push

### Database connection fails
- Make sure database is linked in **Storage** tab
- Verify `POSTGRES_URL` is set in environment variables
- Check database isn't in sleep mode (free tier pauses after inactivity)

### Cron jobs not running
- Check **Cron Jobs** in settings
- Verify they're enabled
- Check function logs in **Deployments** → **Functions**

### API returns 500 errors
- Check function logs: **Deployments** → **Functions** → Click on a function → **Logs**
- Common issues:
  - Missing environment variables
  - Database connection issues
  - Twilio credentials wrong

### Twilio errors
- Verify all 4 Twilio variables are set correctly
- Check Twilio console for error logs
- Make sure phone numbers are in E.164 format (+1...)

## Success! 🎉

Once everything works:
- You can register via SMS
- Create alerts for specific addresses
- Receive SMS when matching 311 reports are filed

## Next Steps

1. Build the Next.js frontend
2. Add more report types
3. Implement payment for paid tier
4. Add email notifications as alternative to SMS
5. Create admin dashboard

---

**Need help?** Check Vercel docs: https://vercel.com/docs
