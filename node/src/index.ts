import express from 'express';
import { IncomingMessage, createServer } from 'http';
import { WebSocket, WebSocketServer } from "ws";
import { HistoryStore } from './historyStore';
import Redis from 'ioredis'
import { createToken, verifyToken } from './tokens'
import { ChatMessage } from './types';
import 'dotenv/config';


const app = express()
const server = createServer(app)
const wss = new WebSocketServer( {server} );
const connections = new Map<string, Set<WebSocket>>();
const redis = new Redis();
const maxHistory = Number(process.env.MAX_HISTORY ?? 10);
const historyStore = new HistoryStore(redis, maxHistory);


function broadcast(data: string, room: string) {
    const roomWebsockets = connections.get(room);
    if (roomWebsockets) {
        for (const conn of roomWebsockets) {
            if (conn.readyState === WebSocket.OPEN) {
                conn.send(data);
            }
        }
    }
}


app.get('/token', (req, res) => {
    const username = req.query.username as string;
    res.json({token: createToken(username)})
});

app.get('/room/:room', (req, res) => {
    const room = req.params.room;
    const token = req.query.token as string;
    res.send(`<!DOCTYPE html>
    <html>
      <body>
        <input id="msg" type="text"/>
        <button onclick="ws.send(document.getElementById('msg').value)">Send</button>
        <ul id="messages"></ul>
        <script>
          const ws = new WebSocket("ws://localhost:8000/ws/${room}?token=${token}");
          ws.onmessage = (event) => {
            try {
                const jsonObject = JSON.parse(event.data);
                if (jsonObject["type"] == "history") {
                  document.getElementById("messages").replaceChildren()
                  for (const val of jsonObject["messages"]) {
                    const li = document.createElement("li");
                    li.textContent = val["sender"] + ": " + val["text"];
                    document.getElementById("messages").appendChild(li);
                  }
                }
                else {
                  const numOfElements = document.getElementById('messages').querySelectorAll('*').length
                  if (numOfElements >= ${maxHistory}) {
                    document.getElementById('messages').querySelector('li:first-child').remove()
                  }
                  const li = document.createElement("li");
                  li.textContent = jsonObject["sender"] + ": " + jsonObject["text"];
                  document.getElementById("messages").appendChild(li);
                }
            } catch (error) {
                
            }
          };
        </script>
      </body>
    </html>`)
});



wss.on('connection', async (ws: WebSocket, request: IncomingMessage) => {
    const url = new URL(request.url ?? '', `http://${request.headers.host}`);
    const room = url.pathname.split('/').pop();
    const token = url.searchParams.get('token');

    if (!room || !token) {
        ws.close(1008);
        return;
    }
    let sender: string;
    try {
        sender = verifyToken(token);
    } catch {
        ws.close(1008);
        return;
    }


    if (!connections.has(room)) {
        connections.set(room, new Set<WebSocket>());
    }
    connections.get(room)?.add(ws)

    const history = await historyStore.get(room);
    ws.send(JSON.stringify({ type: 'history', messages: history }))

    ws.on('message', async (data: Buffer) => {
        const text = data.toString();
        const message: ChatMessage = {
            text: text,
            sender: sender
        }
        await historyStore.push(room, message)
        broadcast(JSON.stringify({type: "message", text: text, sender: sender}), room);
    });
    ws.on('close', () => {
        const roomWebsockets = connections.get(room);
        if (roomWebsockets) {
            roomWebsockets.delete(ws);
            if (roomWebsockets.size === 0) {
                connections.delete(room)
            }
        }
    });
});


server.listen(8000)