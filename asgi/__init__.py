import socketio
from routes import sio


app = socketio.ASGIApp(sio)

