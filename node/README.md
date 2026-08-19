# Broadcast Server — Node

TypeScript/Node implementation of the broadcast server. See the
[top-level README](../README.md) for the design, message protocol, and known limitations
shared by all implementations.

## Stack

- **Language:** TypeScript (Node 24)
- **HTTP + WebSocket:** Express + `ws` (sharing one HTTP server)
- **History:** Redis (`ioredis`)
- **Auth:** `jsonwebtoken` (HS256)
- **Deployment:** multi-stage Docker (build TS → run plain JS), Docker Compose

## Quick start

```bash
cp .env.example .env    # fill JWT_SECRET, REDIS_HOST, MAX_HISTORY, ACCESS_TOKEN_TTL_MINUTES
docker compose up --build
```

Then:
- Get a demo token: `GET http://localhost:8000/token?username=alice`
- Open `http://localhost:8000/room/general?token=<token>` in two tabs
- Type in one — it appears in both; open `/room/other?token=<token>` to see room isolation

Local (without Docker): `npm install`, run Redis, then `npm run dev` (uses `tsx`).

<!-- TODO: sprawdź port -->

## Structure

```
src/
├── index.ts          # Express + ws server, WS endpoint, /token, /room served HTML
├── historyStore.ts   # Redis adapter (RPUSH+LTRIM pipeline, LRANGE)
├── tokens.ts         # JWT create/verify
└── types.ts          # ChatMessage (shared message shape)
```

## Known limitations (in addition to the top-level ones)

- **No tests yet.** The Python implementation has a pytest suite; the Node port does not
  cover the connection/broadcast logic with tests yet.