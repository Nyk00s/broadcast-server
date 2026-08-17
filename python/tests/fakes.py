

class FakeWebSocket:
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail
    async def send_json(self, data):
        if self.fail:
            raise Exception("dead")
        self.sent.append(data)


class FakeHistoryStore:
    def __init__(self, messages=None):
        self.messages = messages or {}
    async def get(self, room): return self.messages.setdefault(room, list())
    async def push(self, room, message): self.messages.setdefault(room, list()).append(message)
