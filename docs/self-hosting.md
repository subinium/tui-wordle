# Self-Hosting Guide

This guide will help you deploy your own TUI Wordle server.

## Prerequisites

- Python 3.11+
- PostgreSQL database (we recommend [Neon](https://neon.tech/) for free hosting)
- Google Cloud account (for OAuth)
- [Railway](https://railway.app/) account (optional, for deployment)

## 1. Database Setup

### Using Neon (Recommended)

1. Create a free account at [neon.tech](https://neon.tech/)
2. Create a new project
3. Copy your connection string:
   ```
   postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/dbname
   ```
4. Convert to async format for SQLAlchemy:
   ```
   postgresql+asyncpg://user:password@ep-xxx.us-east-1.aws.neon.tech/dbname
   ```

### Using Local PostgreSQL

```bash
# Create database
createdb wordle

# Connection string
postgresql+asyncpg://localhost/wordle
```

## 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API" or "Google Identity"
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Select "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:9876/callback` (for local TUI client)
   - `https://your-domain.com/admin/` (for admin dashboard)
7. Copy **Client ID** and **Client Secret**

## 3. Local Development

```bash
# Clone the repository
git clone https://github.com/subinium/tui-wordle.git
cd tui-wordle

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies (with server extras)
pip install -e ".[server,dev]"

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/wordle
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
ADMIN_EMAILS=your-email@gmail.com
EOF

# Run database migrations
alembic upgrade head

# Seed daily words
python scripts/seed_database.py

# Start the server
uvicorn server.main:app --reload
```

Server will be available at `http://localhost:8000`

### Running the Client

```bash
# Point to local server
export WORDLE_API_URL=http://localhost:8000

# Run the game
python -m client.app
```

## 4. Production Deployment (Railway)

### Quick Deploy

1. Fork this repository
2. Go to [Railway](https://railway.app/)
3. Create new project → Deploy from GitHub repo
4. Add environment variables in Railway dashboard

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL URL | `postgresql+asyncpg://...` |
| `SECRET_KEY` | Random 32+ char string | `your-secret-key-here` |
| `GOOGLE_CLIENT_ID` | OAuth client ID | `xxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | OAuth secret | `GOCSPX-xxx` |
| `ADMIN_EMAILS` | Admin email list | `admin@example.com,admin2@example.com` |
| `CORS_ORIGINS` | Allowed origins | `*` |

### Railway Configuration

The `railway.toml` is already configured:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "alembic upgrade head && uvicorn server.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
```

## 5. Admin Dashboard

Access the admin dashboard at `https://your-domain.com/admin/`

Features:
- View server statistics
- Manage daily words
- View all users
- View leaderboard

**Note:** You must add your email to `ADMIN_EMAILS` to access the admin dashboard.

## 6. Generating Words

### Generate new year's words

```bash
# Generate words for 2027
python scripts/generate_words.py --year 2027 --output data/words_2027.json

# Upload to database
python scripts/seed_database.py --file data/words_2027.json
```

### Word file format

```json
[
  {"date": "2027-01-01", "word": "CRANE"},
  {"date": "2027-01-02", "word": "SLATE"},
  ...
]
```

## 7. API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | Simple username login |
| `GET /auth/google/auth-url` | Get Google OAuth URL |
| `POST /auth/google/callback` | Handle OAuth callback |
| `GET /words/today` | Get today's word |
| `POST /games/submit` | Submit game result |
| `GET /leaderboard/today` | Today's leaderboard |
| `GET /streaks/me` | Get user's streak |
| `GET /stats/me` | Get user's statistics |

## Troubleshooting

### "Google OAuth not configured"

Make sure both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set.

### "Admin access required"

Add your email to `ADMIN_EMAILS` environment variable.

### Database connection errors

- Check your `DATABASE_URL` format
- Ensure the database exists
- Run `alembic upgrade head` to create tables

### OAuth redirect errors

Make sure your redirect URI is added to Google Cloud Console:
- For TUI: `http://localhost:9876/callback`
- For Admin: `https://your-domain.com/admin/`

## Support

- [GitHub Issues](https://github.com/subinium/tui-wordle/issues)
- [Discussions](https://github.com/subinium/tui-wordle/discussions)
