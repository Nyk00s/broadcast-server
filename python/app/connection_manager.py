from fastapi import WebSocket
from app.history_store import HistoryStore
import json


class ConnectionManager:
    """
    The Connection manager for handling connections in separate rooms, disconnections, and broadcasting messages to clients
    """
    def __init__(self, history_store: HistoryStore):
        self.connections: dict[str, set] = dict()
        self.history_store = history_store

    async def broadcast(self, message: str, room: str):
        await self.history_store.push(room, message)
        for conn in list(self.connections.get(room, set())):
            try:
                await conn.send_json({
                    "type": "message",
                    "text": message,
                })
            except Exception:
                self.connections.get(room, set()).discard(conn)

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self.connections.setdefault(room, set()).add(websocket)
        data = await self.history_store.get(room)
        messages = self._transform_messages_into_dict(data)
        await websocket.send_json({
            "type": "history",
            "messages": messages
        })

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.connections:
            self.connections[room].discard(websocket)
            if not self.connections[room]:
                del self.connections[room]

    def _transform_messages_into_dict(self, messages: list) -> list[dict[str, str]]:
        result = []
        for mess in messages:
            text_val = mess.decode("utf-8") if isinstance(mess, bytes) else mess
            result.append(
                {
                    "text": text_val
                }
            )
        return result
        