from socketio import AsyncNamespace
from bson import ObjectId
import json
from datetime import datetime
from database import Database


class ChatNamespace(AsyncNamespace):
    
    async def on_connect(self, sid: str, environ: dict):
        query_str = environ.get("QUERY_STRING", None)
        if not query_str or "user_id" not in query_str:
            return self.disconnect(sid)
        query = self.parse_query_string(query_str)
        user_id = query["user_id"]
        self.enter_room(sid, user_id)
        messages = self.get_unread_messages(user_id)
        return await self.emit("unread_messages", messages, room=sid)

    def on_disconnect(self, sid: str):
        print("disconnected ", sid)
        
    def parse_query_string(self, query_string:str):
        return {k: v for k, v in [i.split("=") for i in query_string.split("&")]}
    
    def get_responce_json(self, mongo_data, is_array=False):
        data = []
        if is_array:
            for i in mongo_data:
                i["_id"] = str(i["_id"])
                i["created_at"] = i["created_at"].isoformat()
                data.append(i)
            return data
        else:
            return json.loads(json.dumps(mongo_data, default=str))
        
    async def on_message(self, sid: str, data: dict):
        print(data)
        keys = ["message", "user_id", "receiver_id"]
        isValid = all([key in data for key in keys])
        
        if not isValid:
            return
        
        with Database() as client:
            user = client.auth.profile.find_one({"_id": data["user_id"]})
            receiver = client.auth.profile.find_one({"_id": data["receiver_id"]})
            
            if not user or not receiver:
                print("user or receiver not found")
                return
            
            message_dict = {
                "message": data["message"],
                "user_id": data["user_id"],
                "receiver_id": data["receiver_id"],
                "name": user.get("name", None),
                "profile_picture": user.get("profile_picture", None),
                "mark_as_read": False,
                "is_delivered": False,
                "created_at": datetime.utcnow()
            }
            
            new_chat = client.chat.messages.insert_one(message_dict)
            
            message_dict["_id"] = str(new_chat.inserted_id)
            message_dict["created_at"] = message_dict["created_at"].isoformat()
            
            await self.emit("message", message_dict, room=data["receiver_id"])
            return await self.emit("message", message_dict, room=sid)
        
    async def on_delivered(self, sid:str, data: dict):
        if "message_ids" not in data:
            return
        with Database() as client:
            ids = [ObjectId(id) for id in data["message_ids"]]
            client.chat.messages.update_many({"_id": {"$in": ids}}, {"$set": {"is_delivered": True}})
            messages = client.chat.messages.find({"_id": {"$in": ids}})
            for message in messages:
                await self.emit("delivered", {"_id": str(message["_id"])}, room=message["user_id"])
        return await self.emit("delivered", data["message_ids"], room=sid)
        
    async def on_mark_as_read(self, sid: str, data: dict):
        keys = ["message_id", "user_id"]
        isValid = all([key in data for key in keys])
        
        if not isValid:
            return
        
        with Database() as client:
            message = client.chat.messages.find_one({"_id": data["message_id"]})
            
            if not message:
                return
            
            if message["receiver_id"] != data["user_id"]:
                return
            
            client.chat.messages.update_one({
                "_id": ObjectId(message["_id"])
            }, {
                "$set": {
                    "mark_as_read": True
                }
            })
            
            return await self.emit("mark_as_read", data["message_id"], room=message["user_id"])
    
    def get_unread_messages(self, user_id):
         with Database() as client:
            messages = client.chat.messages.find({
                "receiver_id": user_id,
                "is_delivered": False
            }).sort("created_at", 1)
            return self.get_responce_json(mongo_data=messages, is_array=True)
    
    async def on_unread_messages(self, sid: str, data: dict):
        
        if "user_id" not in data:
            return

        messages = self.get_unread_messages(data["user_id"])    
        return await self.emit("unread_messages", messages, room=sid)
    
    # get all messages between two users in pagination format
    async def on_previous_messages(self, sid: str, data: dict):
        
        keys = ["user_id", "receiver_id", "page"]
        isValid = all([key in data for key in keys])
        
        if not isValid:
            return
        
        PAGE_SIZE = 10
        
        with Database() as client:
            
            query = {
               "user_id": {
                   "$in": [data["user_id"], data["receiver_id"]]
               },
               "receiver_id": {
                   "$in": [data["user_id"], data["receiver_id"]]
               }
            }
            
            messages = client.chat.messages.find(query)
            
            messages_count = client.chat.messages.count_documents(query)
            
            paginated_messages = messages.sort("created_at", -1).skip((data["page"] - 1) * PAGE_SIZE).limit(PAGE_SIZE)
            paginated_messages = self.get_responce_json(mongo_data=paginated_messages, is_array=True)
            
            response = {
                "messages": paginated_messages,
                "meta": {
                    "messages_count": len(paginated_messages),
                    "page": data["page"],
                    "can_load_more": messages_count > data["page"] * PAGE_SIZE
                }
            }
            
            return await self.emit("previous_messages", response, room=sid)
        
