# FinShield AI — Cloud & Infrastructure Notes

## Current Deployment Target

### Frontend
- **Local dev:** `npm run dev` → http://localhost:3000
- **Production target:** Vercel (free tier)
- **Build command:** `next build`
- **Output:** Static + SSR (Next.js App Router)

### Backend (PENDING)
- **Local dev:** `uvicorn app.main:app --reload --port 8000`
- **Production target:** Railway or Render (free tier)
- **Docker:** `backend/Dockerfile` (to be created)

### Database
- **Primary:** Supabase (PostgreSQL) — free tier (500 MB, 2 CPU)
- **URL format:** `postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
- **Required env vars:**
  - `DATABASE_URL`
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_KEY`

### Cache (PENDING)
- **Primary:** Redis (Redis Cloud free tier or Railway Redis)
- **URL:** `redis://localhost:6379/0`

### Notifications
- **Email:** Resend.com (3,000/month free) — `RESEND_API_KEY`
- **SMS:** Twilio (paid, ~₹0.10/SMS) — `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`
- **Push:** Firebase FCM (free) — `FIREBASE_SERVICE_ACCOUNT_JSON`

## Environment Variables Required

### Frontend `.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[ANON_KEY]
```

### Backend `.env`
```
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=[ANON_KEY]
SUPABASE_SERVICE_KEY=[SERVICE_KEY]
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=[RANDOM_64_CHARS]
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
RESEND_API_KEY=re_[KEY]
EMAIL_FROM=noreply@finshield.ai
TWILIO_ACCOUNT_SID=AC[SID]
TWILIO_AUTH_TOKEN=[TOKEN]
TWILIO_FROM_NUMBER=+1[NUMBER]
ENCRYPTION_KEY=[32_BYTE_BASE64]
ML_MODEL_PATH=app/ml/models
APP_ENV=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000
```

## Notes
- Supabase free tier is sufficient for development and demo
- All external service API keys are optional (graceful degradation)
- ML models stored in Supabase Storage (`.pkl`, `.onnx` files)
