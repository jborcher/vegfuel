# VegFuel API — Setup & Running Guide

## 1. Prerequisites
- Python 3.11+
- PostgreSQL (or a Supabase project)
- A Supabase project (free tier works fine): https://supabase.com

## 2. Install dependencies
```bash
cd vegfuel-api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

Get your values from: Supabase dashboard → Settings → API

## 4. Set up the database
The app auto-creates tables on startup in development.
For production, use Alembic migrations:

```bash
pip install alembic
alembic init migrations
# Edit migrations/env.py to import your Base and models
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

## 5. Run the API
```bash
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

## 6. Social Login Setup

### Google
1. Go to https://console.cloud.google.com
2. Create OAuth 2.0 credentials (Web application)
3. Add your domain to authorized JavaScript origins
4. Use the client ID in your frontend Google Sign-In button

### Apple
1. Go to https://developer.apple.com
2. Create a Services ID under your App ID
3. Enable Sign In with Apple
4. Update the `audience` in `auth.py` with your bundle ID:
   `audience="com.yourcompany.vegfuel"`

## 7. Deployment (Render.com — easiest)
1. Push code to GitHub
2. New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from your .env
6. Use Render's managed PostgreSQL or point to Supabase

## API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Email/password signup |
| POST | /auth/login | Email/password login |
| POST | /auth/social | Google or Apple login |
| GET | /users/me | Get current user profile |
| PATCH | /users/me | Update profile/goals/weight |
| GET | /logs/{date} | Get food log for a date |
| POST | /logs/sync | Bulk sync local log to server |
| DELETE | /logs/{date}/{id} | Delete a single log entry |
| DELETE | /logs/{date} | Clear entire day |
| GET | /mixtures/ | List all saved mixtures |
| POST | /mixtures/ | Create or update a mixture |
| PUT | /mixtures/{id} | Update mixture by ID |
| DELETE | /mixtures/{id} | Delete a mixture |
| GET | /ingredients/ | List custom ingredients |
| POST | /ingredients/ | Create or update ingredient |
| DELETE | /ingredients/{id} | Delete a custom ingredient |
