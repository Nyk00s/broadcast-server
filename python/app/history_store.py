from redis.asyncio import Redis
import json

class HistoryStore:
    """Cache client for managing cache operations"""
    def __init__(self, client: Redis, max_history: int):
        self.client = client
        self.max_history = max_history

    async def get(self, room: str) -> str:
        key = f"history:{room}"
        data = await self.client.lrange(key, 0, -1)
        return [json.loads(message) for message in data]


    async def push(self, room: str, message: dict):
        key = f"history:{room}"
        pipeline = self.client.pipeline()
        pipeline.rpush(key, json.dumps(message))
        pipeline.ltrim(key, -self.max_history, -1)
        await pipeline.execute()
        