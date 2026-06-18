from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.security import create_access_token

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/token", response_model=TokenResponse)
async def get_token(body: TokenRequest):
    """
    Gera um token de acesso via client credentials.
    client_id e client_secret são definidos no .env do servidor.
    """
    if body.client_id != settings.CLIENT_ID or body.client_secret != settings.CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="client_id ou client_secret inválidos.",
        )
    return TokenResponse(
        access_token=create_access_token(),
        expires_in=settings.TOKEN_EXPIRE_HOURS * 3600,
    )
