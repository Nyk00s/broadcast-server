import logging
from fastapi import WebSocket


class ConnectionManager:
    """
    The Connection manager for handling connections in separate rooms, disconnections, and broadcasting messages to clients
    """
    def __init__(self):
        self.connections: dict[str, set] = dict()

    async def broadcast(self, message: str, room: str):
        for conn in list(self.connections.get(room, set())):
            try:
                await conn.send_text(message)
            except Exception:
                self.connections[room].discard(conn)
        logging.info(f"message: {message} sent")

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self.connections.setdefault(room, set()).add(websocket)
        logging.info("client connected")

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.connections:
            self.connections[room].discard(websocket)
            if not self.connections[room]:
                del self.connections[room]
        logging.info("client disconnected")
        