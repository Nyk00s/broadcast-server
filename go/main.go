package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/gorilla/websocket"
	"github.com/redis/go-redis/v9"
)

func parseIntOrDefault(s string, def int64) int64 {
	val, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		return def
	}
	return val
}

var maxHistory int64 = parseIntOrDefault(os.Getenv("MAX_HISTORY"), 10)
var hs = HistoryStore{
	Client:     redis.NewClient(&redis.Options{Addr: fmt.Sprintf("%v:%v", os.Getenv("CACHE_HOST"), os.Getenv("CACHE_PORT"))}),
	maxHistory: maxHistory,
}
var manager = Manager{
	rooms: make(map[string]map[*websocket.Conn]bool),
	hs:    hs,
}
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}
var appPort string = os.Getenv("APP_PORT")

func getRoomFromPath(path string, prefix string) string {
	return strings.TrimPrefix(path, prefix)
}

func handleWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("upgrade error", err)
		return
	}
	defer conn.Close()
	room := getRoomFromPath(r.URL.Path, "/ws/room/")
	token := r.URL.Query().Get("token")
	sub, err := verifyToken(token)
	if err != nil {
		conn.WriteMessage(websocket.CloseMessage,
			websocket.FormatCloseMessage(1008, "unauthorized"))
		return
	}

	err = manager.addConnection(room, conn)
	if err != nil {
		conn.WriteMessage(websocket.CloseMessage,
			websocket.FormatCloseMessage(1011, "internal error"))
		return
	}
	for {
		_, data, err := conn.ReadMessage()
		if err != nil {
			manager.removeConnection(room, conn)
			break
		}
		err = manager.broadcast(room, data, sub)
		if err != nil {
			return
		}
	}
}

func handleRoom(w http.ResponseWriter, r *http.Request) {
	room := getRoomFromPath(r.URL.Path, "/room/")
	token := r.URL.Query().Get("token")
	html := fmt.Sprintf(`<!DOCTYPE html>
    <html>
      <body>
        <input id="msg" type="text"/>
        <button onclick="ws.send(document.getElementById('msg').value)">Send</button>
        <ul id="messages"></ul>
        <script>
          const ws = new WebSocket("ws://localhost:%v/ws/%v?token=%v");
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
                  if (numOfElements >= %v) {
                    document.getElementById('messages').querySelector('li:first-child').remove()
                  }
                  const li = document.createElement("li");
                  li.textContent = jsonObject["message"]["sender"] + ": " + jsonObject["message"]["text"];
                  document.getElementById("messages").appendChild(li);
                }
            } catch (error) {
                
            }
          };
        </script>
      </body>
    </html>`, appPort, room, token, maxHistory)
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprint(w, html)
}

func handleToken(w http.ResponseWriter, r *http.Request) {
	username := r.URL.Query().Get("username")
	if username == "" {
		username = "Anonymous"
	}
	token, err := createToken(username)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data := map[string]string{
		"token": token,
	}
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func main() {
	http.HandleFunc("/ws/", handleWS)
	http.HandleFunc("/room/", handleRoom)
	http.HandleFunc("/token", handleToken)
	log.Println("listening on :", appPort)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%v", appPort), nil))
}
