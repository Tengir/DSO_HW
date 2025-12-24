from __future__ import annotations

import json
import logging
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.adapters.repositories import (
    InMemoryDeckRepository,
    SessionStore,
    UserRepository,
)
from app.config import settings
from app.domain.models import Deck, User
from app.errors import problem_response
from app.schemas import (
    DeckCreatePayload,
    DeckEnvelope,
    DeckListEnvelope,
    DeckListResponse,
    DeckUpdatePayload,
    LoginPayload,
    RegisterPayload,
    TokenResponse,
    UserEnvelope,
    UserResponse,
    deck_to_response,
)
from app.services.auth import AuthService
from app.services.decks import DeckService
from app.shared.errors import ApiError

app = FastAPI(title="SecDev Course App", version="0.1.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return problem_response(
        request=request,
        status_code=exc.status,
        title="Application error",
        detail=exc.message,
        type_=f"error:{exc.code}",
        code=exc.code,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return problem_response(
        request=request,
        status_code=exc.status_code,
        title="HTTP error",
        detail=detail,
        type_="about:blank",
        code="http_error",
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return problem_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation error",
        detail="payload validation failed",
        type_="about:blank",
        code="validation_error",
        extra={"details": exc.errors()},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid4()))
    started = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - started) * 1000)
    response.headers["X-Request-Id"] = request_id
    logger.info(
        json.dumps(
            {
                "ts": time.time(),
                "level": "INFO",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


user_repo = UserRepository()
session_store = SessionStore()
auth_service = AuthService(user_repo=user_repo, sessions=session_store)

deck_repo = InMemoryDeckRepository()
deck_service = DeckService(deck_repo=deck_repo)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> User:
    auth_header = request.headers.get("Authorization")
    token = None
    if credentials is not None:
        token = credentials.credentials
    elif auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise ApiError(code="unauthorized", message="missing bearer token", status=401)
    return auth_service.get_user_by_token(token)


def assert_owner_or_admin(user: User, deck: Deck) -> None:
    if user.role != "admin" and deck.owner_id != user.id:
        raise ApiError(code="forbidden", message="not your deck", status=403)


@app.post(
    "/api/v1/auth/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserEnvelope,
)
def register_endpoint(payload: RegisterPayload):
    role = "user"
    if settings.admin_email and payload.email.lower() == settings.admin_email.lower():
        role = "admin"
    record = auth_service.register_user(
        email=payload.email,
        password=payload.password,
        locale=payload.locale,
        proficiency_level=payload.proficiency_level,
        role=role,
    )
    return UserEnvelope(
        user=UserResponse(
            id=record.id,
            email=record.email,
            role=record.role,
            locale=record.locale,
            proficiency_level=record.proficiency_level,
        )
    )


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login_endpoint(payload: LoginPayload):
    token = auth_service.authenticate(email=payload.email, password=payload.password)
    return TokenResponse(access_token=token)


@app.post(
    "/api/v1/decks",
    status_code=status.HTTP_201_CREATED,
    response_model=DeckEnvelope,
)
def create_deck_endpoint(
    payload: DeckCreatePayload, current_user: User = Depends(get_current_user)
):
    deck = deck_service.create_deck(owner=current_user, payload=payload)
    return DeckEnvelope(deck=deck_to_response(deck))


@app.get("/api/v1/decks", response_model=DeckListEnvelope)
def list_decks_endpoint(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    decks = deck_service.list_decks()
    if current_user.role != "admin":
        decks = [deck for deck in decks if deck.owner_id == current_user.id]
    total = len(decks)
    items = decks[offset : offset + limit]
    return DeckListEnvelope(
        decks=DeckListResponse(
            items=[deck_to_response(deck) for deck in items],
            limit=limit,
            offset=offset,
            total=total,
        )
    )


@app.get("/api/v1/decks/{deck_id}", response_model=DeckEnvelope)
def get_deck_endpoint(deck_id: str, current_user: User = Depends(get_current_user)):
    deck = deck_service.get_deck(deck_id)
    assert_owner_or_admin(current_user, deck)
    return DeckEnvelope(deck=deck_to_response(deck))


@app.patch("/api/v1/decks/{deck_id}", response_model=DeckEnvelope)
def update_deck_endpoint(
    deck_id: str,
    payload: DeckUpdatePayload,
    current_user: User = Depends(get_current_user),
):
    deck = deck_service.get_deck(deck_id)
    assert_owner_or_admin(current_user, deck)
    updated = deck_service.update_deck(deck, payload)
    return DeckEnvelope(deck=deck_to_response(updated))


@app.delete("/api/v1/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck_endpoint(deck_id: str, current_user: User = Depends(get_current_user)):
    deck = deck_service.get_deck(deck_id)
    assert_owner_or_admin(current_user, deck)
    deck_service.delete_deck(deck_id)
