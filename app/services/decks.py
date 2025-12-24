from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from uuid import uuid4

from app.adapters.repositories import DeckRepository
from app.domain.models import Deck, User
from app.shared.errors import ApiError

if TYPE_CHECKING:
    from app.schemas import DeckCreatePayload, DeckUpdatePayload


class DeckService:
    def __init__(self, deck_repo: DeckRepository):
        self._deck_repo = deck_repo

    def create_deck(self, owner: User, payload: "DeckCreatePayload") -> Deck:
        # Нормализация UTC: используем timezone-aware datetime
        now = datetime.now(timezone.utc).replace(tzinfo=None)
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

    def get_deck(self, deck_id: str) -> Deck:
        deck = self._deck_repo.get(deck_id)
        if deck is None:
            raise ApiError(code="not_found", message="deck not found", status=404)
        return deck

    def list_decks(self) -> List[Deck]:
        return self._deck_repo.list_all()

    def update_deck(self, deck: Deck, payload: "DeckUpdatePayload") -> Deck:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        updated = Deck(
            id=deck.id,
            owner_id=deck.owner_id,
            title=payload.title.strip() if payload.title is not None else deck.title,
            description=(
                payload.description.strip()
                if payload.description is not None
                else deck.description
            ),
            source_lang=(
                payload.source_lang.lower()
                if payload.source_lang is not None
                else deck.source_lang
            ),
            target_lang=(
                payload.target_lang.lower()
                if payload.target_lang is not None
                else deck.target_lang
            ),
            created_at=deck.created_at,
            updated_at=now,
        )
        return self._deck_repo.save(updated)

    def delete_deck(self, deck_id: str) -> None:
        self._deck_repo.delete(deck_id)
