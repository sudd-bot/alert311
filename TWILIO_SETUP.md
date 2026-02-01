# Twilio Setup Guide for Alert311

This guide will walk you through setting up Twilio for phone verification and SMS alerts.

## What You Need from Twilio

1. **Account SID** - Your Twilio account identifier
2. **Auth Token** - Secret key for API access
3. **Verify Service SID** - For phone number verification
4. **Phone Number** - For sending SMS alerts

## Step-by-Step Setup

### 1. Create Twilio Account

1. Go to https://www.twilio.com/try-twilio
2. Sign up for a free trial account
3. Verify your email and phone number
4. You'll get **$15 in free credit** (enough for ~500 SMS messages)

### 2. Get Your Account SID and Auth Token

1. After signing in, you'll see the Twilio Console dashboard
2. Look for the **Account Info** panel on the right side
3. Copy these values:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click the eye icon to reveal, starts with random chars)

**Save these!** You'll need them for your `.env` file:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
```

### 3. Create a Verify Service

The Verify service handles SMS verification codes for phone numbers.

1. In the Twilio Console, go to **Explore Products** (left sidebar)
2. Find and click **Verify** → Click **Create new service**
3. Enter a **Friendly Name**: `Alert311 Phone Verification`
4. Click **Create**
5. Copy the **Service SID** (starts with `VA...`)

**Save this:**
```
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Verify Settings (Optional but Recommended):**
- Click on your new service
- Go to **Settings**
- Set **Code Length**: 6 (default is good)
- Set **Code Expiration**: 10 minutes (default)
- **Fraud Guard**: Leave enabled (free protection)

### 4. Get a Phone Number

You need a phone number to send SMS alerts from.

#### Option A: Free Trial Number (Easiest)

1. Go to **Phone Numbers** → **Manage** → **Buy a number**
2. Choose **United States** as country
3. Check **SMS** capability
4. Click **Search**
5. Pick any number you like
6. Click **Buy** (uses trial credit, no charge)
7. Copy the phone number (format: `+1234567890`)

**Save this:**
```
TWILIO_FROM_NUMBER=+12345678901
```

#### Option B: Use Your Trial Number

Twilio gives you a trial number automatically. Find it at:
- **Phone Numbers** → **Manage** → **Active numbers**

**Trial Limitations:**
- Can only send SMS to verified numbers (numbers you've verified in the console)
- Messages will include "Sent from your Twilio trial account" prefix

To verify test numbers:
1. Go to **Phone Numbers** → **Manage** → **Verified Caller IDs**
2. Click **Add a new Caller ID**
3. Enter your test phone number

### 5. Update Your Environment File

Add all the credentials to your `.env` file:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+12345678901
```

### 6. Test Your Setup

Run the test script to verify everything works:

```bash
cd ~/workspace/sudd-bot/alert311/backend
python scripts/test_services.py
```

Or test manually with a quick Python script:

```python
from twilio.rest import Client

account_sid = "ACxxxx"  # Your Account SID
auth_token = "your_token"  # Your Auth Token

client = Client(account_sid, auth_token)

# Test SMS
message = client.messages.create(
    body="Test from Alert311!",
    from_="+12345678901",  # Your Twilio number
    to="+16464171584"      # Your phone number
)

print(f"Message sent! SID: {message.sid}")
```

## Cost Breakdown

### Trial Account ($15 credit)
- **Verify API**: $0.05 per verification (300 verifications)
- **SMS (US)**: $0.0079 per message (~1,900 messages)

### After Trial
- **Pay-as-you-go**: No monthly fees, only pay for usage
- Same rates as above
- Can add auto-recharge ($20 minimum)

### Estimated Costs for Alert311

**Per user signup:**
- 1 verification: $0.05
- Average alerts: Let's say 2-3 per month
- Monthly cost per user: ~$0.07

**For 100 active users:**
- ~$7/month in SMS costs
- Very affordable!

## Upgrade to Full Account (When Ready)

When you're ready to go live:

1. **Upgrade** in the console (removes trial restrictions)
2. Add payment method (credit card)
3. Set up **auto-recharge** (optional but recommended)
4. Request **increased rate limits** if needed (default is 60 SMS/second)

## Security Best Practices

⚠️ **Never commit your tokens to Git!**

- Keep `.env` in `.gitignore` ✅
- Use Vercel environment variables for production
- Rotate tokens if they're ever exposed
- Enable **Two-Factor Authentication** on your Twilio account

## Troubleshooting

### "Unverified number" error
- You're on a trial account
- Either verify the recipient number in Twilio Console, or upgrade your account

### "Invalid phone number"
- Use E.164 format: `+1` + area code + number
- Example: `+16464171584` (not `646-417-1584`)

### "Insufficient balance"
- Trial credit ran out
- Add payment method to continue

### Verification codes not arriving
- Check SMS logs in Twilio Console → **Monitor** → **Logs** → **Verify**
- Verify the phone number is in E.164 format
- Check if the number is blocked/invalid

## Next Steps

Once Twilio is set up:

1. ✅ Test the verification flow: `POST /auth/register`
2. ✅ Test SMS alerts locally
3. 🚀 Deploy to Vercel
4. 📱 Test end-to-end with a real 311 report

## Support

- **Twilio Docs**: https://www.twilio.com/docs
- **Verify API**: https://www.twilio.com/docs/verify/api
- **Support**: https://support.twilio.com (requires account)

---

Need help? The Twilio Console has excellent error messages and logs!
