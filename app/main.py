from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, constr, field_validator

from app.errors import problem_response

logger = logging.getLogger(__name__)

app = FastAPI(title="SecDev Course App", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик всех необработанных исключений.

    Гарантирует, что stack trace никогда не попадёт в ответ пользователю,
    но полная информация логируется для разработчиков.
    """
    # Логируем полную информацию об ошибке (для разработчиков)
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
        extra={
            "path": str(request.url),
            "method": request.method,
        },
    )

    # Возвращаем безопасный ответ без внутренних деталей
    return problem_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal server error",
        detail="An unexpected error occurred. Please try again later.",
        type_="error:internal",
        code="internal_error",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Domain layer (simplified for the initial slice) ---


@dataclass(frozen=True)
class User:
    id: str
    email: str
    role: str
    locale: str
    proficiency_level: str


@dataclass(frozen=True)
class Deck:
    id: str
    owner_id: str
    title: str
    description: Optional[str]
    source_lang: str
    target_lang: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Note:
    id: str
    deck_id: str
    fields: Dict[str, str]
    tags: List[str] = field(default_factory=list)
    media_refs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Card:
    id: str
    note_id: str
    deck_id: str
    card_type: str
    template_id: str
    created_at: datetime


@dataclass(frozen=True)
class UserCardState:
    id: str
    user_id: str
    card_id: str
    status: str
    stability: float
    retrievability: float
    ease_factor: float
    interval: int
    next_review_at: Optional[datetime]
    last_review_at: Optional[datetime]
    review_count: int
    success_count: int
    lapses_count: int


# --- Repository and service layer ---


class DeckRepository:
    def save(self, deck: Deck) -> Deck:
        raise NotImplementedError


class InMemoryDeckRepository(DeckRepository):
    def __init__(self):
        self._storage: Dict[str, Deck] = {}

    def save(self, deck: Deck) -> Deck:
        self._storage[deck.id] = deck
        return deck


class DeckService:
    def __init__(self, deck_repo: DeckRepository):
        self._deck_repo = deck_repo

    def create_deck(self, owner: User, payload: "DeckCreatePayload") -> Deck:
        now = datetime.utcnow()
        deck = Deck(
            id=str(uuid4()),
            owner_id=owner.id,
            title=payload.title.strip(),
            description=payload.description.strip() if payload.description else None,
            source_lang=payload.source_lang.lower(),
            target_lang=payload.target_lang.lower(),
            created_at=now,
            updated_at=now,
        )
        return self._deck_repo.save(deck)


deck_repo = InMemoryDeckRepository()
deck_service = DeckService(deck_repo=deck_repo)


# --- Schemas and dependencies ---


class DeckCreatePayload(BaseModel):
    """Схема для создания колоды с строгой валидацией входных данных."""

    model_config = {"extra": "forbid"}  # Запрещаем лишние поля

    title: constr(min_length=1, max_length=100)
    description: Optional[constr(max_length=500)] = None
    source_lang: constr(min_length=2, max_length=2)
    target_lang: constr(min_length=2, max_length=2)

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Проверяет, что код языка состоит из 2 символов (ISO 639-1)."""
        v_lower = v.lower().strip()
        if len(v_lower) != 2:
            raise ValueError("language code must be exactly 2 characters (ISO 639-1)")
        return v_lower


class DeckResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    description: Optional[str] = None
    source_lang: str
    target_lang: str
    created_at: datetime
    updated_at: datetime


class DeckEnvelope(BaseModel):
    deck: DeckResponse


def deck_to_response(deck: Deck) -> DeckResponse:
    return DeckResponse(
        id=deck.id,
        owner_id=deck.owner_id,
        title=deck.title,
        description=deck.description,
        source_lang=deck.source_lang,
        target_lang=deck.target_lang,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
    )


def get_current_user() -> User:
    # In a real app this would validate a JWT/session.
    return User(
        id="00000000-0000-0000-0000-000000000001",
        email="student@example.com",
        role="user",
        locale="ru",
        proficiency_level="b1",
    )


# --- API layer ---


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
