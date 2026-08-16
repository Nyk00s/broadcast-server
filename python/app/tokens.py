import jwt
from app.config import Config
from datetime import datetime, timezone, timedelta

settings = Config()


def create_access_token(user: str):
    return jwt.encode(
        payload={
            "sub": user,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_ttl_minutes),
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }, 
        key=settings.jwt_secret.get_secret_value(), 
        algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> dict:
    return jwt.decode(
        jwt=token, 
        key=settings.jwt_secret.get_secret_value(), 
        algorithms=[settings.jwt_algorithm]
    )
