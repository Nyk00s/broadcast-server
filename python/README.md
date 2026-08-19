# Broadcast Server — Python

Python implementation of the broadcast server. See the
[top-level README](../README.md) for the design, message protocol, and known limitations
shared by all implementations.

## Stack

- **Server:** FastAPI (native WebSocket support), uvicorn
- **History:** Redis (`redis.asyncio`)
- **Auth:** pyjwt (HS256)
- **Tests:** pytest
- **Deployment:** Docker Compose

## Quick start

```bash
cp .env.example .env    # fill JWT_SECRET (see below)
docker compose up --build
```

Then:
- Get a demo token: `POST http://localhost:8000/token?username=alice`
- Open `http://localhost:8000/room/general?token=<token>` in two tabs
- Type in one — it appears in both; open `/room/other?token=<token>` to see room isolation

<!-- TODO: sprawdź port (compose/.env). Wygeneruj JWT_SECRET: -->
> Generate `JWT_SECRET`: `python -c "import secrets; print(secrets.token_hex(32))"`

## Structure

<!-- TODO: dostosuj do faktycznych plików -->
```
app/
├── main.py                # FastAPI app, WS endpoint, /token, /room served HTML
├── connection_manager.py  # rooms (dict[room -> set]), broadcast, connect/disconnect
├── history_store.py       # Redis adapter (RPUSH+LTRIM pipeline, LRANGE)
├── tokens.py              # JWT create/verify
└── config.py              # settings (pydantic-settings)
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Cover `ConnectionManager` with in-memory fakes (fake `HistoryStore`, fake WebSocket):
room cleanup on disconnect, broadcast to all, behaviour when a connection is dead.