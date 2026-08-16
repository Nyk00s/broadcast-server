from redis.asyncio import Redis

class HistoryStore:
    """Cache client for managing cache operations"""
    def __init__(self, client: Redis, max_history: int):
        self.client = client
        self.max_history = max_history

    async def get(self, room: str) -> str:
        key = f"history:{room}"
        return await self.client.lrange(key, 0, -1)

    async def push(self, room: str, message: str):
        key = f"history:{room}"
        pipeline = self.client.pipeline()
        pipeline.rpush(key, message)
        pipeline.ltrim(key, -self.max_history, -1)
        await pipeline.execute()
        