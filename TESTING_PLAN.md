# Alert311 - Testing Plan

**Status:** Waiting for Twilio A2P Campaign Approval  
**ETA:** 1-4 weeks from campaign submission

---

## ⏳ Blocked Until A2P Approval

### SMS-Dependent Features
These features require the Twilio A2P campaign to be approved:

1. **Phone Verification**
   - Endpoint: `POST /auth/register`
   - Uses: Twilio Verify API (should work, but testing shows errors)
   - Status: ⏳ Needs real phone + approved campaign

2. **SMS Alerts**
   - Endpoint: Cron job `/cron/send-alerts`
   - Uses: Twilio Messages API (blocked by A2P)
   - Status: ⏳ Waiting for campaign approval

---

## ✅ Ready to Test Now (No SMS Required)

### API Health Checks
```bash
# App info
curl https://backend-sigma-nine-42.vercel.app/

# Health check
curl https://backend-sigma-nine-42.vercel.app/health

# API documentation
open https://backend-sigma-nine-42.vercel.app/docs
```

### Database Operations
- Database tables created ✅
- Connection working ✅
- Models defined ✅

### Frontend UI
- Map loads ✅
- Address search UI ready ✅
- Alert creation form ready ✅
- Frontend at: https://www.alert311.com

---

## 🧪 Manual Testing Checklist (When SMS Ready)

### Phase 1: Phone Verification
```bash
# 1. Register phone number
curl -X POST 'https://backend-sigma-nine-42.vercel.app/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{"phone": "+16464171584"}'

# Expected: SMS with verification code sent
# Response: {"message": "Verification code sent"}

# 2. Check phone for SMS code (6 digits)

# 3. Verify code
curl -X POST 'https://backend-sigma-nine-42.vercel.app/auth/verify' \
  -H 'Content-Type: application/json' \
  -d '{"phone": "+16464171584", "code": "123456"}'

# Expected: User created in database
# Response: {"message": "Phone verified successfully", "user_id": "..."}
```

### Phase 2: Create Alert
```bash
# Create alert for specific address
curl -X POST 'https://backend-sigma-nine-42.vercel.app/alerts?phone=+16464171584' \
  -H 'Content-Type: application/json' \
  -d '{
    "address": "555 Market St, San Francisco, CA",
    "report_types": ["Parking on Sidewalk"]
  }'

# Expected: Alert created in database
# Response: {"message": "Alert created", "alert_id": "..."}
```

### Phase 3: Test Alert Flow
1. **Create test alert** for a known location
2. **Wait for cron job** to poll SF 311 API (runs every 5 min)
3. **Check if matching report** triggers SMS
4. **Verify SMS received** at registered phone

---

## 🔬 Technical Testing (No SMS Required)

### Database Queries
```bash
# Connect to Neon console and check:
SELECT * FROM users;
SELECT * FROM alerts;
SELECT * FROM reports;

# Verify indexes and constraints
\d users
\d alerts
\d reports
```

### API Endpoint Coverage
- ✅ `GET /` - App info
- ✅ `GET /health` - Health check
- ✅ `GET /docs` - API documentation
- ⏳ `POST /auth/register` - Needs SMS
- ⏳ `POST /auth/verify` - Needs SMS
- ⏳ `POST /alerts` - Needs verified user
- ⏳ `GET /alerts` - Needs verified user
- ⏳ `POST /cron/poll-reports` - Ready, needs testing
- ⏳ `POST /cron/send-alerts` - Blocked by A2P

### SF 311 API Integration
```bash
# Test polling SF 311 API directly
curl -X POST 'https://backend-sigma-nine-42.vercel.app/cron/poll-reports' \
  -H 'Authorization: Bearer 91924a3e4b51f3d8b1ec42201753177d4de427f6b493c4c87f64e7c36d4b5532'

# Should fetch reports from SF 311 and cache in database
# Check: SELECT * FROM reports; to see if data populated
```

---

## 🎯 Post-Approval Testing Sequence

### 1. Immediate Testing (Day 1)
- [ ] Register phone number via API
- [ ] Verify SMS code received
- [ ] Create test alert
- [ ] Verify alert saved in database

### 2. Short-Term Testing (Week 1)
- [ ] Test cron job for polling reports
- [ ] Test cron job for sending alerts
- [ ] Verify SMS alerts received
- [ ] Test multiple alerts per user
- [ ] Test alert editing/deletion

### 3. Load Testing (Week 2)
- [ ] Register multiple users
- [ ] Create multiple alerts
- [ ] Monitor database performance
- [ ] Check Twilio usage/costs
- [ ] Monitor Vercel function execution times

---

## 📊 Success Criteria

### MVP (Minimum Viable Product)
- ✅ User can register phone number
- ✅ User receives SMS verification code
- ✅ User can create alert for address
- ✅ System polls SF 311 API every 5 min
- ✅ User receives SMS when matching report filed

### Nice to Have
- [ ] User can view all their alerts
- [ ] User can edit/delete alerts
- [ ] User can choose multiple report types
- [ ] Frontend shows alerts on map
- [ ] Email notifications as alternative

---

## 🐛 Known Issues to Test

1. **ESLint warning** in frontend build (cosmetic)
2. **API domain auth** (requires manual fix)
3. **Cold start times** (Vercel functions ~300-500ms)
4. **Rate limits** (need to test Twilio limits)
5. **Database connection pooling** (test under load)

---

## 📝 Testing Notes

### Twilio Limits
- **Verify API:** Typically no A2P restrictions
- **Messages API:** Blocked until A2P campaign approved
- **Rate limits:** Monitor in Twilio console
- **Costs:** ~$0.0075 per SMS sent

### SF 311 API
- **No authentication** required for read-only
- **Rate limits:** Unknown, monitor for errors
- **Data freshness:** Real-time from SF 311 system

### Database
- **Neon Postgres:** Serverless, scales automatically
- **Connection pooling:** Enabled via DATABASE_URL
- **SSL required:** Already configured

---

## ✅ When A2P Approved

1. **Notify me:** I'll get a message via hourly cron check
2. **Run Phase 1 tests:** Phone verification flow
3. **Run Phase 2 tests:** Alert creation
4. **Run Phase 3 tests:** End-to-end alert flow
5. **Monitor:** Check logs, database, Twilio usage
6. **Document:** Update STATUS.md with test results

---

**Current Status:** Infrastructure ready, waiting on Twilio A2P campaign approval. All non-SMS features can be tested immediately. SMS-dependent features ready to test as soon as campaign is approved.
