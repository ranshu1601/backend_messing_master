from socketio import AsyncServer
from controllers.in_room import InRoomMessaging
from controllers.chat import ChatNamespace

sio = AsyncServer(async_mode="asgi")

sio.register_namespace(InRoomMessaging("/in_room"))
sio.register_namespace(ChatNamespace("/chat"))
