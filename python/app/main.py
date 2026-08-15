from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.connection_manager import ConnectionManager
from fastapi.responses import HTMLResponse
from app.config import Config
from redis import Redis
from app.history_store import HistoryStore

settings = Config()
app = FastAPI()
manager = ConnectionManager(
    HistoryStore(Redis(settings.cache_host, settings.cache_port), settings.max_history)
)


@app.websocket('/ws/{room}')
async def handle_connections(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, room)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


@app.get('/room/{room}')
async def get(room: str):
    return HTMLResponse(
        f'''
    <!DOCTYPE html>
    <html>
      <body>
        <input id="msg" type="text"/>
        <button onclick="ws.send(document.getElementById('msg').value)">Send</button>
        <ul id="messages"></ul>
        <script>
          const ws = new WebSocket("ws://localhost:8000/ws/{room}");
          ws.onmessage = (event) => {{
            try {{
                const jsonObject = JSON.parse(event.data);
                if (jsonObject[\"type\"] == \"history\") {{
                  document.getElementById("messages").replaceChildren()
                  for (const val of jsonObject[\"messages\"]) {{
                    const li = document.createElement("li");
                    li.textContent = val[\"text\"];
                    document.getElementById("messages").appendChild(li);
                  }}
                }}
                else {{
                  const numOfElements = document.getElementById('messages').querySelectorAll('*').length
                  if (numOfElements >= {settings.max_history}) {{
                    document.getElementById('messages').querySelector('li:first-child').remove()
                  }}
                  const li = document.createElement("li");
                  li.textContent = jsonObject[\"text\"];
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
