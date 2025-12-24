from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


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
