import pytest
from app.connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_disconnect_last_user_and_delete_connections_room(make_fake_history_store, make_fake_websocket):
    websocket = make_fake_websocket()
    manager = ConnectionManager(make_fake_history_store())
    await manager.connect(websocket, 'fake_room')

    manager.disconnect(websocket, 'fake_room')

    assert 'fake_room' not in manager.connections


@pytest.mark.asyncio
async def test_disconnect_one_of_two_users_connection_stays(make_fake_history_store, make_fake_websocket):
    websocket = make_fake_websocket()
    websocket1 = make_fake_websocket()
    manager = ConnectionManager(make_fake_history_store())
    await manager.connect(websocket, 'fake_room')
    await manager.connect(websocket1, 'fake_room')

    manager.disconnect(websocket, 'fake_room')

    assert 'fake_room' in manager.connections


@pytest.mark.asyncio
async def test_broadcast_sends_message_to_all_connected_users(make_fake_history_store, make_fake_websocket):
    websocket = make_fake_websocket()
    websocket1 = make_fake_websocket()
    manager = ConnectionManager(make_fake_history_store())
    await manager.connect(websocket, 'fake_room')
    await manager.connect(websocket1, 'fake_room')

    await manager.broadcast("random_message", 'fake_room', 'user')

    assert websocket.sent
    assert websocket.sent[-1]['text'] == 'random_message'
    assert websocket.sent[-1]['sender'] == 'user'
    assert websocket1.sent
    assert websocket1.sent[-1]['text'] == 'random_message'
    assert websocket1.sent[-1]['sender'] == 'user'



@pytest.mark.asyncio
async def test_connect_propagates_error_when_client_dead_during_join(make_fake_history_store, make_fake_websocket):
    websocket = make_fake_websocket(fail=True)
    manager = ConnectionManager(make_fake_history_store())

    with pytest.raises(Exception):
        await manager.connect(websocket, 'fake_room')
