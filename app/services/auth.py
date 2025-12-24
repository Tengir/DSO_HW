from app.adapters.repositories import SessionStore, UserRepository
from app.domain.models import User
from app.shared.errors import ApiError
from app.shared.security import verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository, sessions: SessionStore):
        self._user_repo = user_repo
        self._sessions = sessions

    def register_user(
        self,
        *,
        email: str,
        password: str,
        locale: str,
        proficiency_level: str,
        role: str = "user",
    ):
        return self._user_repo.create_user(
            email=email,
            password=password,
            role=role,
            locale=locale,
            proficiency_level=proficiency_level,
        )

    def authenticate(self, *, email: str, password: str) -> str:
        record = self._user_repo.get_by_email(email)
        if record is None:
            raise ApiError(
                code="unauthorized", message="invalid credentials", status=401
            )
        if not verify_password(password, record.password_salt, record.password_hash):
            raise ApiError(
                code="unauthorized", message="invalid credentials", status=401
            )
        return self._sessions.create(record.id)

    def get_user_by_token(self, token: str) -> User:
        user_id = self._sessions.get_user_id(token)
        if user_id is None:
            raise ApiError(code="unauthorized", message="invalid token", status=401)
        record = self._user_repo.get_by_id(user_id)
        if record is None:
            raise ApiError(code="unauthorized", message="invalid token", status=401)
        return record.to_user()
