#!/bin/bash
echo "929d383c10e36fa98f7676d8c9afdba2" | vercel env add TWILIO_AUTH_TOKEN production
echo "VAa1a35f4332eccf74a7190ad00ba0f79f" | vercel env add TWILIO_VERIFY_SERVICE_SID production
echo "+16508440850" | vercel env add TWILIO_FROM_NUMBER production
echo "91924a3e4b51f3d8b1ec42201753177d4de427f6b493c4c87f64e7c36d4b5532" | vercel env add CRON_SECRET production
echo "postgresql://neondb_owner:npg_SXMiK7O0cQyA@ep-jolly-feather-ahvhen01-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require" | vercel env add DATABASE_URL production
echo "postgresql://neondb_owner:npg_SXMiK7O0cQyA@ep-jolly-feather-ahvhen01-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require" | vercel env add POSTGRES_URL production
