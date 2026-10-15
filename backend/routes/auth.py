"""JWT Authentication routes."""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import APIRouter, HTTPException, Depends, Header
from jose import JWTError, jwt

from core.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from core.schemas import UserCreate, UserLogin, TokenResponse
from database import SessionLocal, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _hash_password(password: str) -> str:
    # bcrypt only handles up to 72 bytes; fail early with a clear API error.
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password is too long (max 72 bytes)")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


@router.post("/register", response_model=TokenResponse)
async def register(req: UserCreate):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == req.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Validate role
        valid_roles = ["noc_engineer", "network_planner", "executive"]
        if req.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        hashed = _hash_password(req.password)
        user = User(username=req.username, hashed_password=hashed, role=req.role)
        db.add(user)
        db.commit()
        db.refresh(user)

        token = _create_access_token({"sub": user.username, "role": user.role})
        return TokenResponse(
            access_token=token,
            username=user.username,
            role=user.role,
        )
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLogin):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not _verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = _create_access_token({"sub": user.username, "role": user.role})
        return TokenResponse(
            access_token=token,
            username=user.username,
            role=user.role,
        )
    finally:
        db.close()


@router.get("/me")
async def me(authorization: str = Header(default=None)):
    """Return current user info from JWT token."""
    from routes.deps import get_current_user_required

    user = await get_current_user_required(authorization)
    return {"username": user["username"], "role": user["role"]}
