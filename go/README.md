# Broadcast Server — Go

Go implementation of the broadcast server. See the
[top-level README](../README.md) for the design, message protocol, and known limitations
shared by all implementations.

## Stack

- **Language:** Go 1.27
- **HTTP + WebSocket:** net/http + gorilla/websocket
- **History:** Redis (go-redis/v9)
- **Auth:** golang-jwt/jwt/v5 (HS256)
- **Deployment:** multi-stage Docker (build static binary → alpine runtime), Docker Compose

## Quick start

```bash
cp .env.example .env    # fill JWT_SECRET, CACHE_HOST/PORT, APP_PORT, MAX_HISTORY
docker compose up --build
```

Then:
- Get a demo token: `GET http://localhost:8000/token?username=alice`
- Open `http://localhost:8000/room/general?token=<token>` in two tabs
- Type in one — it appears in both; open `/room/other?token=<token>` for room isolation

Local (without Docker): run Redis, set the env vars, then `go run .`

## Structure

```
main.go           # HTTP server, WS/room/token handlers, wiring from env
manager.go        # Manager: rooms map + mutex, addConnection/broadcast/removeConnection
historystore.go   # Redis adapter (RPUSH+LTRIM pipeline, LRANGE), Message + json tags
tokens.go         # JWT create/verify
```

## Notes on this implementation

- Concurrency model: net/http runs each connection in its own goroutine (real
parallelism), each with a blocking for{ReadMessage} loop — unlike the single
event loop of Python/Node. Shared state (the rooms map) is guarded by a mutex.
- Broadcast holds the mutex through the whole iteration, so it needs no copy of the
connection set (contrast: Python copies because await interleaves; Node doesn't
because send is synchronous; Go doesn't because the lock is held).
- Dead connections: a failed WriteJSON closes + deletes that connection mid-range and
keeps going, so one dead client doesn't stop delivery to the rest.
- Deploys as a single static binary (CGO_ENABLED=0) into a tiny alpine image — the
runtime image contains no Go toolchain, just the compiled server.


## Known limitations (in addition to the top-level ones)

- **No tests yet.** (Same as the Node implementation; the Python one has a pytest suite.)
- **JWT secret not validated at startup** — an unset `JWT_SECRET` yields an empty signing
  key with no warning.