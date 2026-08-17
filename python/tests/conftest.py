import pytest
from fakes import FakeWebSocket, FakeHistoryStore


@pytest.fixture
def make_fake_websocket():
    def _make(fail: bool = False):
        return FakeWebSocket(fail)
    return _make


@pytest.fixture
def make_fake_history_store():
    def _make(messages: dict = None):
        return FakeHistoryStore(messages)
    return _make
