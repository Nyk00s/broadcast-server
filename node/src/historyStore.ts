import Redis from 'ioredis'
import { ChatMessage } from './types.js';

export class HistoryStore {
    private redis: Redis
    private maxHistory: number

    constructor(redis: Redis, maxHistory: number) {
        this.redis = redis;
        this.maxHistory = maxHistory;
    }

    async get(room: string): Promise<ChatMessage[]> {
        const key = `history:${room}`;
        const data = await this.redis.lrange(key, 0, -1);
        return data.map((m) => JSON.parse(m));
    }

    async push(room: string, message: ChatMessage): Promise<void> {
        const key = `history:${room}`;
        const pipeline = this.redis.pipeline()
        pipeline.rpush(key, JSON.stringify(message));
        pipeline.ltrim(key, -this.maxHistory, -1);
        await pipeline.exec();
    }

}