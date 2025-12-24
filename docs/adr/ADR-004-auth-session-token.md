## ADR-004: Session-based auth with opaque tokens

### Context

Для MVP нужен простой и безопасный механизм аутентификации без лишней сложности.
JWT потребует настройки подписи, TTL и обновления токенов, что не так просто.

### Decision

Используем session-based auth:
- при логине выдаём случайный opaque-токен;
- токен хранится в in-memory хранилище;
- клиент передаёт токен в заголовке `Authorization: Bearer <token>`.

### Consequences

Плюсы:
- минимальная сложность реализации;
- удобно для MVP.

Минусы:
- токены теряются при перезапуске приложения;
- не подходит для масштабирования без общего хранилища.

### Links

- **Код:** `app/main.py`, `app/services/auth.py`, `app/adapters/repositories.py`
