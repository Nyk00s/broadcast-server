from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from app.connection_manager import ConnectionManager
from fastapi.responses import HTMLResponse
from app.config import Config
from redis.asyncio import Redis
from app.history_store import HistoryStore
from app.tokens import create_access_token, decode_token
import jwt
import logging

settings = Config()
app = FastAPI()
manager = ConnectionManager(
    HistoryStore(Redis(host=settings.cache_host, port=settings.cache_port, decode_responses=True), settings.max_history)
)


@app.post('/token')
async def issue_token(username: str):
    return {"token": create_access_token(username)}


@app.websocket('/ws/{room}')
async def handle_connections(websocket: WebSocket, room: str):
    await websocket.accept()
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=1008)
        logging.error("Invalid Token")
        return
    try:
      payload = decode_token(token)
    except jwt.InvalidTokenError:
        await websocket.close(1008)
        logging.error("Invalid Token")
        return
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, room, payload['sub'])
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


@app.get('/room/{room}')
async def get(room: str, token: str = Query()):
    return HTMLResponse(
        f'''
    <!DOCTYPE html>
    <html>
      <body>
        <input id="msg" type="text"/>
        <button onclick="ws.send(document.getElementById('msg').value)">Send</button>
        <ul id="messages"></ul>
        <script>
          const ws = new WebSocket("ws://localhost:8000/ws/{room}?token={token}");
          ws.onmessage = (event) => {{
            try {{
                const jsonObject = JSON.parse(event.data);
                if (jsonObject["type"] == "history") {{
                  document.getElementById("messages").replaceChildren()
                  for (const val of jsonObject["messages"]) {{
                    const li = document.createElement("li");
                    li.textContent = val["sender"] + ": " + val["text"];
                    document.getElementById("messages").appendChild(li);
                  }}
                }}
                else {{
                  const numOfElements = document.getElementById('messages').querySelectorAll('*').length
                  if (numOfElements >= {settings.max_history}) {{
                    document.getElementById('messages').querySelector('li:first-child').remove()
                  }}
                  const li = document.createElement("li");
                  li.textContent = jsonObject["sender"] + ": " + jsonObject["text"];
                  document.getElementById("messages").appendChild(li);
                }}
            }} catch (error) {{
                
            }}
          }};
        </script>
      </body>
    </html>
    '''
    )
