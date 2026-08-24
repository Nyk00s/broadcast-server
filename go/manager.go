package main

import (
	"context"
	"sync"
	"github.com/gorilla/websocket"
)

type JSONMessage struct {
	Type    string  `json:"type"`
	Message Message `json:"message"`
}

type JSONHistory struct {
	Type     string    `json:"type"`
	Messages []Message `json:"messages"`
}

type Manager struct {
	mu    sync.Mutex
	rooms map[string]map[*websocket.Conn]bool
	hs    HistoryStore
}

func (m *Manager) addConnection(room string, ws *websocket.Conn) error {
	m.mu.Lock()
	websockets, ok := m.rooms[room]
	if !ok {
		websockets = make(map[*websocket.Conn]bool)
		m.rooms[room] = websockets
	}
	websockets[ws] = true
	m.mu.Unlock()
	messages, err := m.hs.get(context.Background(), room)
	if err != nil {
		return err
	}

	jsonHistory := JSONHistory{Type: "history", Messages: messages}
	err = ws.WriteJSON(jsonHistory)
	if err != nil {
		return err
	}
	return nil
}

func (m *Manager) broadcast(room string, message []byte, sender string) error {
	messageStructure := Message{Text: string(message), Sender: sender}
	err := m.hs.push(context.Background(), room, messageStructure)
	if err != nil {
		return err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	for conn := range m.rooms[room] {
		jsonMessage := JSONMessage{Type: "message", Message: messageStructure}
		if err = conn.WriteJSON(jsonMessage); err != nil {
			conn.Close()
			delete(m.rooms[room], conn)
		}
	}
	return nil
}

func (m *Manager) removeConnection(room string, ws *websocket.Conn) {
	m.mu.Lock()
	defer m.mu.Unlock()

	websockets, ok := m.rooms[room]
	if !ok {
		return
	}

	delete(websockets, ws)
	if len(websockets) == 0 {
		delete(m.rooms, room)
	}
}
