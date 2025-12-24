from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Dict, List, Optional
from uuid import uuid4

from app.domain.models import Deck, User
from app.shared.errors import ApiError
from app.shared.security import hash_password


@dataclass(frozen=True)
class UserRecord:
    id: str
    email: str
    role: str
    locale: str
    proficiency_level: str
    password_hash: str
    password_salt: str

    def to_user(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            role=self.role,
            locale=self.locale,
            proficiency_level=self.proficiency_level,
        )


class UserRepository:
    def __init__(self):
        self._by_id: Dict[str, UserRecord] = {}
        self._by_email: Dict[str, UserRecord] = {}

    def get_by_email(self, email: str) -> Optional[UserRecord]:
        return self._by_email.get(email.lower())

    def get_by_id(self, user_id: str) -> Optional[UserRecord]:
        return self._by_id.get(user_id)

    def create_user(
        self,
        *,
        email: str,
        password: str,
        role: str,
        locale: str,
        proficiency_level: str,
    ) -> UserRecord:
        normalized_email = email.lower()
        if self.get_by_email(normalized_email) is not None:
            raise ApiError(code="conflict", message="user already exists", status=409)

        salt = secrets.token_hex(16)
        password_hash = hash_password(password, salt)
        record = UserRecord(
            id=str(uuid4()),
            email=normalized_email,
            role=role,
            locale=locale,
            proficiency_level=proficiency_level,
            password_hash=password_hash,
            password_salt=salt,
        )
        self._by_id[record.id] = record
        self._by_email[record.email] = record
        return record


class SessionStore:
    def __init__(self):
        self._tokens: Dict[str, str] = {}

    def create(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = user_id
        return token

    def get_user_id(self, token: str) -> Optional[str]:
        return self._tokens.get(token)


class DeckRepository:
    def save(self, deck: Deck) -> Deck:
        raise NotImplementedError

    def get(self, deck_id: str) -> Optional[Deck]:
        raise NotImplementedError

    def list_all(self) -> List[Deck]:
        raise NotImplementedError

    def delete(self, deck_id: str) -> None:
        raise NotImplementedError


class InMemoryDeckRepository(DeckRepository):
    def __init__(self):
        self._storage: Dict[str, Deck] = {}

    def save(self, deck: Deck) -> Deck:
        self._storage[deck.id] = deck
        return deck

    def get(self, deck_id: str) -> Optional[Deck]:
        return self._storage.get(deck_id)

    def list_all(self) -> List[Deck]:
        return list(self._storage.values())

    def delete(self, deck_id: str) -> None:
        self._storage.pop(deck_id, None)
