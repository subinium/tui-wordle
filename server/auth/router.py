import httpx
import secrets
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from server.database import get_db
from server.config import get_settings
from server.auth.schemas import (
    UserCreate,
    TokenResponse,
    GoogleAuthUrlResponse,
    GoogleCallbackRequest,
    GoogleCallbackResponse,
)
from server.auth.service import create_or_get_user, create_or_get_google_user

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Simple username-based login."""
    user, token = await create_or_get_user(db, user_data.username)
    return TokenResponse(id=user.id, username=user.username, token=token)


@router.get("/google/auth-url", response_model=GoogleAuthUrlResponse)
async def google_auth_url(redirect_uri: str):
    """Get Google OAuth authorization URL."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return GoogleAuthUrlResponse(auth_url=auth_url, state=state)


@router.post("/google/callback", response_model=GoogleCallbackResponse)
async def google_callback(
    request: GoogleCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback - exchange code for token and get user info."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": request.code,
                "grant_type": "authorization_code",
                "redirect_uri": request.redirect_uri,
            },
        )

        if token_response.status_code != 200:
            return GoogleCallbackResponse(
                success=False,
                error=f"Failed to exchange code: {token_response.text}"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return GoogleCallbackResponse(
                success=False,
                error="No access token received"
            )

        # Get user info
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            return GoogleCallbackResponse(
                success=False,
                error="Failed to get user info"
            )

        userinfo = userinfo_response.json()
        google_id = userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name")
        avatar_url = userinfo.get("picture")

        if not google_id or not email:
            return GoogleCallbackResponse(
                success=False,
                error="Invalid user info from Google"
            )

        # Create or get user
        user, token = await create_or_get_google_user(
            db,
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )

        return GoogleCallbackResponse(
            success=True,
            user_id=user.id,
            username=user.username,
            token=token,
        )


@router.get("/google/status")
async def google_status():
    """Check if Google OAuth is configured."""
    return {
        "configured": bool(settings.google_client_id and settings.google_client_secret)
    }
