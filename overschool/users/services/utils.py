from datetime import datetime, timedelta
from typing import Any

import jwt

from overschool import settings


class JWTHandler:
    def create_access_token(
        self, subject: str | Any, expires_delta: timedelta | None = None
    ) -> str:
        if expires_delta is not None:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, settings.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(
        self, subject: str | Any, expires_delta: timedelta | None = None
    ) -> str:
        if expires_delta is not None:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_REFRESH_SECRET_KEY, settings.ALGORITHM
        )
        return encoded_jwt
