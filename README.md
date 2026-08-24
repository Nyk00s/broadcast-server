# Broadcast Server

Real-time broadcast/chat server built on WebSockets: clients connect to rooms and every
message is broadcast to all other members of the same room, with JWT auth and Redis-backed
message history.

---

## Implementations

The same server is implemented in two languages, sharing the design and protocol below:

- **Python** — FastAPI, `redis.asyncio`. See [`python/`](./python).
- **Node** — TypeScript, Express + `ws`, `ioredis`. See [`node/`](./node).
- **Go** — net/http + gorilla/websocket, go-redis. See [`go/`](./go).

---

## Features

- WebSocket connections grouped into rooms (a message reaches only its room)
- Broadcast to all clients in a room, resilient to dead connections
- JWT authentication on connect (unauthenticated clients are rejected before joining)
- Message history per room (new clients receive the last N messages on join)
- Redis-backed history, shared store (though live broadcast is single-instance)

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
Broadcasting to a room must tolerate the connection set changing while it iterates — but each language reaches that safety differently. Python (asyncio) and Node run on a single-threaded event loop: Python awaits each send, so it iterates over a copy of the set; Node sends synchronously, so its loop runs atomically over the live set. Go is different — each connection runs in its own goroutine with real parallelism, so the shared connection map is guarded by a mutex held across the whole broadcast, which is what makes iterating the live set safe there. Same problem, three idioms: copy, synchronous send, and lock.


### Auth verified before joining
The client's connection is accepted, then the JWT is verified, and only then is the client joined to a room. If the token is invalid, the client is rejected before joining.


### Redis for history
History is stored in Redis rather than in process memory. This keeps it in a separate process, so it survives restarts of the application server and is shared rather than tied to one process. Each room is a Redis list; on every message the server does RPUSH + LTRIM in a pipeline, which keeps only the last N messages atomically - the durable equivalent of a deque(maxlen=N).


### HistoryStore abstraction
The connection-handling layer doesn't know history lives in Redis — it receives a HistoryStore via dependency injection and works with plain message objects. Swapping the storage backend wouldn't require changing the broadcast logic.

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

- Redis Pub/Sub for multi-instance broadcast
- First-message auth handshake (token out of the URL)
