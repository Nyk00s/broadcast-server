from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.connection_manager import ConnectionManager
from fastapi.responses import HTMLResponse

app = FastAPI()
manager = ConnectionManager()


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
            const li = document.createElement("li");
            li.textContent = event.data;
            document.getElementById("messages").appendChild(li);
          }};
        </script>
      </body>
    </html>
    '''
    )
