# Broadcast Server

Real-time broadcast/chat server built on WebSockets: clients connect to rooms and every
message is broadcast to all other members of the same room, with JWT auth and Redis-backed
message history.

---

## Features

- WebSocket connections grouped into rooms (a message reaches only its room)
- Broadcast to all clients in a room, resilient to dead connections
- JWT authentication on connect (unauthenticated clients are rejected before joining)
- Message history per room (new clients receive the last N messages on join)
- Redis-backed history (survives restarts, shared across processes)

---

## Stack

- **Language:** Python 3.14
- **Server:** FastAPI (native WebSocket support), uvicorn
- **History store:** Redis
- **Auth:** pyjwt (HS256)
- **Deployment:** Docker Compose

---

## Quick start

```bash
git clone git@github.com:Nyk00s/broadcast-server.git
cd broadcast-server/python

cp .env.example .env    # fill JWT_SECRET (see below)

docker compose up --build
```

- Server: http://localhost:8000
- Open two browser tabs to test:
  1. Get a demo token: `POST http://localhost:8000/token?username=alice`
  2. Open `http://localhost:8000/room/<room-name>?token=<paste-token>` in two tabs
  3. Type in one - it appears in both (same room)
  4. Open `http://localhost:8000/room/other?token=<token>` - it does NOT see previous one

> Generate `JWT_SECRET` with:
> `python -c "import secrets; print(secrets.token_hex(32))"`

---

## Message protocol

Server → client, on join (history):
```json
{ "type": "history", "messages": [ { "text": "hi", "sender": "alice" } ] }
```

Server → client, on new message:
```json
{ "type": "message", "text": "hello", "sender": "bob" }
```

Client → server: plain text (the message body).

---

## Design decisions

### WebSockets over REST

In REST the server cannot push data on its own - it only responds to client requests. Broadcast requires the server to push a message to many clients the moment it arrives, so it needs a persistent, bidirectional connection: a WebSocket.


### Concurrency model (asyncio)
Asyncio runs on a single thread and switches between tasks only at await points, so code between two awaits runs without interruption. In broadcast, await connection.send(...) is such a point: while a send is awaited, another coroutine - for example a client disconnecting - can run and modify the set of connections. That's why broadcast iterates over a copy of the set, so the original can safely change mid-iteration. Each send is also wrapped in try/except, so a single dead connection is discarded without breaking delivery to the rest.


### Auth verified before joining
The client's connection is accepted, then the JWT is verified, and only then is the client joined to a room. If the token is invalid, the client is rejected before joining.

### Redis for history
History is stored in Redis rather than in process memory. This keeps it in a separate process, so it survives restarts of the application server and is shared rather than tied to one process. Each room is a Redis list; on every message the server does RPUSH + LTRIM in a pipeline, which keeps only the last N messages atomically - the durable equivalent of a deque(maxlen=N).

### HistoryStore abstraction
The ConnectionManager doesn't know the history lives in Redis - it receives a HistoryStore via dependency injection and works with plain dicts. Swapping the storage backend wouldn't require changing the manager.

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Tests covers methods from ConnectionManager: cleaning empty rooms, broadcasting, behavior when websocket is dead.

---

## Known limitations

- **Single instance only.** History is shared via Redis, but WebSocket connections live in
  one process - a message broadcast on one server instance does not reach clients connected
  to another.
- **Token in query parameter.** The JWT travels in the URL (of both the page and the WS
  connection), so it can end up in logs. A first-message auth handshake or a subprotocol
  header would avoid this.
- **Demo token endpoint.** `/token` issues a token for any username with no password - it
  stands in for a real login/identity service.

---

## What can be added

- Ports of the same server to Go and Node (same problem, different concurrency models)
- Redis Pub/Sub for multi-instance broadcast
- First-message auth handshake (token out of the URL)
