# SF 311 OAuth Token Management

**Implemented:** 2026-02-03  
**Status:** ✅ Complete and deployed

---

## Overview

Alert311 now automatically manages SF 311 OAuth tokens for both guest users and authenticated users. Tokens are acquired programmatically (no browser/user interaction needed) and refreshed automatically to prevent expiration.

## Architecture

### Two-Tier Token System

**1. System Token** (for guests)
- Shared by all unauthenticated users
- Used for address searches on the homepage
- Stored in `system_config` table
- Refreshed every 12 hours via cron job
- Can be regenerated freely (SF 311 allows unlimited tokens)

**2. User Tokens** (for verified users)
- One token per user
- Automatically assigned when phone number is verified
- Stored in `User.sf311_*` fields
- Auto-refreshed before expiration (5-minute buffer)
- Proactively refreshed by cron if expiring within 24 hours

## Components

### Database

**SystemConfig Model** (`app/models/system_config.py`)
```python
class SystemConfig:
    key: str (primary)           # e.g., "sf311_system_token"
    value: str                   # JSON: {access_token, refresh_token, ...}
    last_updated_timestamp: int  # Unix timestamp
    created_at, updated_at       # Auto-managed timestamps
```

**User Model** (existing fields)
```python
class User:
    sf311_access_token: str
    sf311_refresh_token: str
    sf311_token_expires_at: int
```

### Services

**TokenManager** (`app/services/token_manager.py`)

Main methods:
- `ensure_system_token_exists(db)` - Initialize system token (called on startup)
- `get_system_token(db)` - Get valid system token (auto-refreshes if needed)
- `get_user_token(user, db)` - Get valid user token (auto-refreshes if needed)
- `assign_token_to_user(user, db)` - Assign new token to user
- `refresh_system_token_proactively(db)` - Cron job: refresh system token
- `refresh_user_tokens_proactively(db)` - Cron job: refresh expiring user tokens

Uses `reporter_lib/auth.py` for programmatic OAuth:
- `auth.acquire_tokens()` - Get brand new token (no browser needed!)
- `auth.refresh_tokens()` - Refresh existing token

### Endpoints

**Startup** (`app/main.py`)
```python
@app.on_event("startup")
- Initializes database
- Ensures system token exists
```

**Phone Verification** (`app/routes/auth.py`)
```python
POST /auth/verify
- Verifies SMS code
- Marks user as verified
- Auto-assigns SF 311 token to user
```

**Token Refresh Cron** (`app/routes/cron.py`)
```python
POST /cron/refresh-tokens
- Refreshes system token
- Refreshes all user tokens expiring within 24h
- Runs every 12 hours (vercel.json)
```

## Token Lifecycle

### System Token

1. **Initialization** (app startup)
   - Check if `sf311_system_token` exists in `system_config`
   - If not, call `auth.acquire_tokens()` to get new token
   - Store in database

2. **On-Demand Refresh** (when accessed)
   - Check if token expires within 5 minutes
   - If yes, call `auth.refresh_tokens()` with refresh_token
   - Update database
   - Fallback: acquire brand new token if refresh fails

3. **Proactive Refresh** (cron job every 12 hours)
   - Refresh system token before expiration
   - Ensures token never expires during usage
   - If refresh fails, acquire brand new token

### User Token

1. **Assignment** (phone verification)
   - User verifies phone with SMS code
   - Call `auth.acquire_tokens()` to get new token
   - Store in `user.sf311_*` fields

2. **On-Demand Refresh** (when used for API calls)
   - Check if token expires within 5 minutes
   - If yes, call `auth.refresh_tokens()` with refresh_token
   - Update user record

3. **Proactive Refresh** (cron job every 12 hours)
   - Find all users with tokens expiring within 24 hours
   - Refresh each user's token
   - Update user records
   - Log failures (but don't block)

## Flow Diagrams

### Guest User (Address Search)

```
Guest → Frontend → Backend API
                      ↓
                  get_system_token()
                      ↓
                  Check if expired
                      ↓
            Yes ──→ Refresh/Acquire
                      ↓
                  Use token for SF 311 API
                      ↓
                  Return results
```

### Verified User (Create Alert)

```
User verifies phone
        ↓
    assign_token_to_user()
        ↓
    auth.acquire_tokens()
        ↓
    Store in user.sf311_*
        ↓
    User creates alert
        ↓
    Cron polls SF 311
        ↓
    get_user_token()
        ↓
    Use token for API
```

## Cron Schedule

**vercel.json:**
```json
{
  "crons": [
    {
      "path": "/cron/poll-reports",
      "schedule": "*/5 * * * *"    // Every 5 minutes
    },
    {
      "path": "/cron/send-alerts",
      "schedule": "*/5 * * * *"     // Every 5 minutes
    },
    {
      "path": "/cron/refresh-tokens",
      "schedule": "0 */12 * * *"    // Every 12 hours
    }
  ]
}
```

## Security

- Tokens stored securely in database (encrypted connection via SSL)
- No tokens exposed to frontend
- Cron endpoints protected with `CRON_SECRET` bearer token
- Automatic refresh prevents stale tokens
- Each user gets own token (no cross-contamination)

## Benefits

✅ **No User Interaction** - Tokens acquired programmatically via `auth.py`  
✅ **Automatic Refresh** - Never deal with expired tokens  
✅ **Scalable** - Per-user tokens prevent rate limiting  
✅ **Guest Support** - System token allows unauthenticated searches  
✅ **Proactive** - Cron job refreshes before expiration  
✅ **Resilient** - Fallback to new token if refresh fails  
✅ **No Rate Limits** - SF 311 allows unlimited token creation  

## Testing

### Check System Token
```bash
# Via database
psql $DATABASE_URL -c "SELECT key, length(value), last_updated_timestamp FROM system_config WHERE key='sf311_system_token';"

# Via API (requires CRON_SECRET)
curl -X POST 'https://backend-sigma-nine-42.vercel.app/cron/refresh-tokens' \
  -H 'Authorization: Bearer <CRON_SECRET>'
```

### Check User Token
```bash
# Via database
psql $DATABASE_URL -c "SELECT phone, sf311_token_expires_at FROM users WHERE sf311_access_token IS NOT NULL;"

# Via API
curl 'https://backend-sigma-nine-42.vercel.app/sf311/token-status?phone=+16464171584'
```

### Manual Token Refresh
```bash
# Trigger cron job manually
curl -X POST 'https://backend-sigma-nine-42.vercel.app/cron/refresh-tokens' \
  -H 'Authorization: Bearer <CRON_SECRET>'
```

## Next Steps

Now that token management is working:

1. ✅ Update `/cron/poll-reports` to use real SF 311 data
2. ✅ Replace mock data in frontend with real reports
3. ✅ Test end-to-end alert flow
4. ⏳ Add frontend "Connect SF 311" button (optional - tokens auto-assigned)

## Troubleshooting

**System token not found error:**
- Solution: Restart app to trigger startup initialization
- Or manually run migration: `python scripts/add_system_config_table.py`

**User token errors after verification:**
- Check logs for token assignment errors
- Verify `reporter_lib/auth.py` is importable
- Ensure SF 311 API is reachable

**Tokens expiring despite cron:**
- Check Vercel cron logs to ensure job is running
- Verify `CRON_SECRET` is set in environment variables
- Manually trigger: `POST /cron/refresh-tokens`

## Migration

**Add system_config table:**
```bash
cd backend
python scripts/add_system_config_table.py
```

**Initialize system token:**
- Automatic on first app startup
- Or call `TokenManager.ensure_system_token_exists(db)`

**Existing users:**
- Will get tokens on next login/verification
- Or manually run: `TokenManager.assign_token_to_user(user, db)`

---

**Documentation:** This file  
**Code:** `app/services/token_manager.py`  
**Tests:** Manual (see Testing section above)
