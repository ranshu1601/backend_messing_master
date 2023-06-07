from socketio import AsyncNamespace
from json import dumps
from datetime import datetime
from database import Database


class InRoomMessaging(AsyncNamespace):
    
    def on_connect(self, sid, environ):
        query_str = environ.get("QUERY_STRING", None)

        if not query_str or "room_code" not in query_str:
            return self.disconnect(sid)
        query = self.parse_query_string(query_str)
        self.enter_room(sid, query["room_code"])
        print('connected to room', query["room_code"])
        
    def on_disconnect(self, sid):
        print('disconnected')
        
   
        
    def parse_query_string(self, query_string:str):
        return {k: v for k, v in [i.split("=") for i in query_string.split("&")]}
        
    async def on_message(self, sid: str, data: dict):
        print("sending message")
        room_code = data.get("room_code", None)
        text_message = data.get("message", None)
        user_id = data.get("user_id", None)
        print(f'room code {room_code} message {text_message} and user id {user_id}')
        if not room_code or not text_message or not user_id:
            print('any field is missing')
            return
        
        with Database() as client:
            roomFromDb = client.myspace.rooms.find_one({"room_code": room_code})
            user = client.auth.profile.find_one({"_id": user_id})
            
            if not roomFromDb or not user:
                return
            
            message_dict = {
                "message": text_message,
                "user_id": user_id,
                "name": user.get("name", None),
                "profile_picture": user.get("profile_picture", None),
                "created_at": datetime.utcnow()
            }
            
            
            message_dict["created_at"] = message_dict["created_at"].isoformat()
            return await self.emit("message", message_dict, room=roomFromDb["room_code"])

