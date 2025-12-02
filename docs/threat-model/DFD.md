# Диаграмма потоков данных (DFD)

## Диаграмма

```mermaid
flowchart TB
    subgraph User["🔵 Trust Boundary: User"]
        U[User]
    end

    subgraph Edge["🟡 Trust Boundary: Edge/API"]
        API[API Gateway<br/>FastAPI]
    end

    subgraph Backend["🟢 Trust Boundary: Backend/Core"]
        Auth[Auth Service<br/>Deck Service]
        DB[(Database<br/>SQLite)]
    end

    U -->|F1: POST /auth/login<br/>{email, password}| API
    U -->|F2: GET /api/v1/decks<br/>{Authorization: Bearer token}| API
    U -->|F3: POST /api/v1/decks<br/>{title, description, langs, token}| API
    U -->|F4: GET /api/v1/decks/{id}<br/>{token}| API
    U -->|F5: POST /api/v1/decks/{id}/cards<br/>{card data, token}| API

    API -->|F6: Проверка токена<br/>{token}| Auth
    API -->|F7: Запрос колод<br/>{user_id}| Auth
    API -->|F8: Создание колоды<br/>{deck data, owner_id}| Auth
    API -->|F9: Запрос колоды<br/>{deck_id, user_id}| Auth
    API -->|F10: Создание карточки<br/>{card data, deck_id, user_id}| Auth

    Auth -->|F11: Проверка пароля<br/>{email, password_hash}| DB
    Auth -->|F12: Сохранение токена<br/>{user_id, token}| DB
    Auth -->|F13: Запрос колод<br/>SELECT decks WHERE owner_id| DB
    Auth -->|F14: Сохранение колоды<br/>INSERT deck| DB
    Auth -->|F15: Запрос колоды<br/>SELECT deck WHERE id, owner_id| DB
    Auth -->|F16: Сохранение карточки<br/>INSERT card| DB

    DB -->|F17: Результат проверки<br/>{user_id, role}| Auth
    DB -->|F18: Список колод<br/>[{deck1, deck2, ...}]| Auth
    DB -->|F19: Данные колоды<br/>{deck}| Auth
    DB -->|F20: Подтверждение сохранения| Auth

    Auth -->|F21: JWT токен<br/>{token}| API
    Auth -->|F22: Список колод<br/>[{deck1, deck2, ...}]| API
    Auth -->|F23: Созданная колода<br/>{deck}| API
    Auth -->|F24: Данные колоды<br/>{deck}| API
    Auth -->|F25: Созданная карточка<br/>{card}| API

    API -->|F26: 200 OK + токен| U
    API -->|F27: 200 OK + список| U
    API -->|F28: 201 Created + колода| U
    API -->|F29: 200 OK + колода| U
    API -->|F30: 201 Created + карточка| U
    API -->|F31: 401/403/422/500 + ошибка| U
```

## Описание потоков

| Поток | Описание | Источник | Получатель |
|-------|----------|----------|------------|
| F1 | Пользователь отправляет логин и пароль для аутентификации | User | API Gateway |
| F2 | Пользователь запрашивает список своих колод с токеном авторизации | User | API Gateway |
| F3 | Пользователь создаёт новую колоду с данными и токеном | User | API Gateway |
| F4 | Пользователь запрашивает конкретную колоду по ID с токеном | User | API Gateway |
| F5 | Пользователь создаёт карточку в колоде с данными и токеном | User | API Gateway |
| F6 | API Gateway проверяет валидность JWT токена | API Gateway | Auth Service |
| F7 | API Gateway запрашивает список колод для пользователя | API Gateway | Auth Service |
| F8 | API Gateway передаёт данные новой колоды с owner_id | API Gateway | Auth Service |
| F9 | API Gateway запрашивает колоду с проверкой owner_id | API Gateway | Auth Service |
| F10 | API Gateway передаёт данные новой карточки с deck_id и user_id | API Gateway | Auth Service |
| F11 | Auth Service проверяет пароль пользователя по email | Auth Service | Database |
| F12 | Auth Service сохраняет токен для пользователя | Auth Service | Database |
| F13 | Auth Service запрашивает колоды пользователя по owner_id | Auth Service | Database |
| F14 | Auth Service сохраняет новую колоду в базу | Auth Service | Database |
| F15 | Auth Service запрашивает колоду с проверкой owner_id | Auth Service | Database |
| F16 | Auth Service сохраняет новую карточку в базу | Auth Service | Database |
| F17 | Database возвращает результат проверки пароля (user_id, role) | Database | Auth Service |
| F18 | Database возвращает список колод пользователя | Database | Auth Service |
| F19 | Database возвращает данные колоды | Database | Auth Service |
| F20 | Database подтверждает успешное сохранение | Database | Auth Service |
| F21 | Auth Service возвращает JWT токен после успешного логина | Auth Service | API Gateway |
| F22 | Auth Service возвращает список колод пользователя | Auth Service | API Gateway |
| F23 | Auth Service возвращает созданную колоду | Auth Service | API Gateway |
| F24 | Auth Service возвращает данные запрошенной колоды | Auth Service | API Gateway |
| F25 | Auth Service возвращает созданную карточку | Auth Service | API Gateway |
| F26 | API Gateway возвращает токен пользователю | API Gateway | User |
| F27 | API Gateway возвращает список колод пользователю | API Gateway | User |
| F28 | API Gateway возвращает созданную колоду пользователю | API Gateway | User |
| F29 | API Gateway возвращает данные колоды пользователю | API Gateway | User |
| F30 | API Gateway возвращает созданную карточку пользователю | API Gateway | User |
| F31 | API Gateway возвращает ошибку (401, 403, 422, 500) пользователю | API Gateway | User |
