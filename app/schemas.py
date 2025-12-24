from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, constr

from app.domain.models import Deck


class RegisterPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: constr(min_length=3, max_length=320)
    password: constr(min_length=8, max_length=128)
    locale: constr(min_length=2, max_length=8) = "ru"
    proficiency_level: constr(min_length=1, max_length=10) = "b1"


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: constr(min_length=3, max_length=320)
    password: constr(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    locale: str
    proficiency_level: str


class UserEnvelope(BaseModel):
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeckCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: constr(min_length=1, max_length=100)
    description: Optional[constr(max_length=500)] = None
    source_lang: constr(min_length=2, max_length=8)
    target_lang: constr(min_length=2, max_length=8)


class DeckUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[constr(max_length=500)] = None
    source_lang: Optional[constr(min_length=2, max_length=8)] = None
    target_lang: Optional[constr(min_length=2, max_length=8)] = None


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


class DeckListResponse(BaseModel):
    items: List[DeckResponse]
    limit: int
    offset: int
    total: int


class DeckListEnvelope(BaseModel):
    decks: DeckListResponse


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
