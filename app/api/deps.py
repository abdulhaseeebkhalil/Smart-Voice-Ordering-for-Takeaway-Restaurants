from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, Query

from app.config import settings


def verify_dashboard_password(
    x_auth_token: Optional[str] = Header(default=None),
    token: Optional[str] = Query(default=None),
) -> None:
    provided = x_auth_token or token
    if not provided or provided != settings.dashboard_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
