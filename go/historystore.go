package main

import (
	"github.com/redis/go-redis/v9"
	"context"
	"encoding/json"
)


type Message struct {
	Text string `json:"text"`
	Sender string `json:"sender"`
}


type HistoryStore struct {
	Client *redis.Client
	maxHistory int64
}


func (hs *HistoryStore) get(ctx context.Context, room string) ([]Message, error) {
	key := "history:" + room
	raw, err := hs.Client.LRange(ctx, key, 0, -1).Result()
	if err != nil {
		return nil, err
	}
	messages := make([]Message, 0, len(raw))
	
	for _, stringMessage := range raw {
		var message Message
		rawMessage := []byte(stringMessage)
		err = json.Unmarshal(rawMessage, &message)
		if err != nil {
			return nil, err
		}
		messages = append(messages, message)
	}
	return messages, nil
}


func (hs *HistoryStore) push(ctx context.Context, room string, message Message) error {

	buffer, err := json.Marshal(message)
	if err != nil {
		return err
	}

	key := "history:" + room
	pipeline := hs.Client.Pipeline()
	pipeline.RPush(ctx, key, string(buffer))
	pipeline.LTrim(ctx, key, -hs.maxHistory, -1)
	_, err = pipeline.Exec(ctx)
	return err
}
