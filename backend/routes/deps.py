"""Shared dependencies for route modules."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt

from core.config import JWT_SECRET_KEY, JWT_ALGORITHM

# ── Global agent references (set during startup in main.py) ──
_agent1 = None
_agent2 = None
_orchestrator = None


def set_globals(agent1, agent2, orchestrator):
    global _agent1, _agent2, _orchestrator
    _agent1 = agent1
    _agent2 = agent2
    _orchestrator = orchestrator


def get_agent1():
    return _agent1


def get_agent2():
    return _agent2


def get_orchestrator():
    return _orchestrator


# ── JWT dependency ──

async def get_current_user_optional(authorization: Optional[str] = Header(default=None)):
    """
    Extract user from JWT if present. Returns None for unauthenticated requests.
    This allows gradual migration: endpoints work without auth but respect tokens.
    """
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "viewer")
        if username is None:
            return None
        return {"username": username, "role": role}
    except JWTError:
        return None


async def get_current_user_required(authorization: Optional[str] = Header(default=None)):
    """Require a valid JWT token. Raises 401 if missing or invalid."""
    user = await get_current_user_optional(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
