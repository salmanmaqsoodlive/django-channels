from channels.consumer import SyncConsumer, AsyncConsumer
import django
django.setup()
from channels.exceptions import StopConsumer
from asgiref.sync import sync_to_async
from accounts.models import Chat, Group, User
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import json
from .serializers import UserSerializer
import base64
import uuid
from django.core.files.base import ContentFile

from accounts.tokenauthentication import JWTAuthentication


class UserNotVerifiedError(Exception):
    pass


class MySyncConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connecting...")
        try:
            user = await self.get_user()
            if user is not None:
                self.user = user
                auth_user, _ = self.user
                user = await database_sync_to_async(User.objects.get)(email=auth_user)
                user_id = user.id
                chat_room = f"user_{user_id}"
                # group = await sync_to_async(Group.objects.get)(name="programmers")
                # chats = []
                # if group:
                #     chats = await database_sync_to_async(list)(
                #         Chat.objects.filter(group=group)
                #     )

                # else:
                #     group = Group(name="programmers")
                #     await database_sync_to_async(group.save)()

                await self.channel_layer.group_add(chat_room, self.channel_name)
                await self.send({"type": "websocket.accept"})
            else:
                self.user = None
        except UserNotVerifiedError as e:
            print(f"Error: {e}")
            raise "User not verified"

    async def websocket_receive(self, event):
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        receiver_id = [
            param.split("=")
            for param in query_string.split("&")
            if param.startswith("receiver_id=")
        ]

        parent_id = [
            param.split("=")
            for param in query_string.split("&")
            if param.startswith("parent_id=")
        ]

        auth_user, _ = self.user
        user = await database_sync_to_async(User.objects.get)(email=auth_user)

        data = json.loads(event["text"])
        message_type = data.get("type")
        message = data.get("message")
        voice_note_data = data.get("voiceNoteData")
        like_data = data.get("likeData")
        file_data = data.get("fileData")

        if message_type == "like":
            print("___________________", like_data)
            receiver_room = f"user_{like_data['receiverId']}"
            sender_room = f"user_{like_data['senderId']}"

            # Fetch the Chat and User objects from the database
            chat = await database_sync_to_async(Chat.objects.get)(
                id=like_data["chatId"]
            )
            user = await database_sync_to_async(User.objects.get)(
                id=like_data["userId"]
            )

            # Modify the Chat object by adding the user to likes
            await database_sync_to_async(chat.likes.add)(user)

            # Save the modified Chat object to the database
            await self.save_chat_to_database(chat)

            # Send a message to the group
            await self.channel_layer.group_send(
                receiver_room,
                {
                    "type": "chat.message",
                    "message": json.dumps(
                        {
                            "userId": user.id,
                            "message": user.first_name + " liked your message",
                        }
                    ),
                    "message_type": message_type,
                    "parent_id": parent_id[0][1],
                },
            )
            await self.channel_layer.group_send(
                sender_room,
                {
                    "type": "chat.message",
                    "message": json.dumps(
                        {
                            "userId": user.id,
                            "message": user.first_name + " liked your message",
                        }
                    ),
                    "message_type": message_type,
                    "parent_id": parent_id[0][1],
                },
            )

        if message_type == "voice_note":
            # Save the voice note data to the database
            chat = Chat(
                receiver_id=receiver_id[0][1],
                sender_id=user.id,
                voice_note_data=voice_note_data,
            )
            await database_sync_to_async(chat.save)()

            # Broadcast the voice note to the sender and receiver
            sender_id = user.id
            sender_room = f"user_{sender_id}"
            receiver_room = f"user_{receiver_id[0][1]}"

            await self.channel_layer.group_send(
                sender_room,
                {
                    "type": "chat.message",
                    "message": voice_note_data,
                    "message_type": message_type,
                },
            )

            await self.channel_layer.group_send(
                receiver_room,
                {
                    "type": "chat.message",
                    "message": voice_note_data,
                    "message_type": message_type,
                },
            )

        elif message_type == "chat":
            sender_id = user.id
            sender_room = f"user_{sender_id}"
            receiver_room = f"user_{receiver_id[0][1]}"

            # Broadcast the message to the sender and receiver
            await self.channel_layer.group_send(
                sender_room,
                {
                    "type": "chat.message",
                    "message": message,
                    "message_type": message_type,
                    "parent_id": parent_id[0][1],
                },
            )

            await self.channel_layer.group_send(
                receiver_room,
                {
                    "type": "chat.message",
                    "message": message,
                    "message_type": message_type,
                    "parent_id": parent_id[0][1],
                },
            )
            # Save the chat message to the database
            chat = Chat(
                content=message,
                receiver_id=receiver_id[0][1],
                sender_id=user.id,
                parent_id=int(parent_id[0][1])
                if parent_id and parent_id[0][1].isdigit()
                else None,
            )
            await database_sync_to_async(chat.save)()
        elif message_type == "file":
            sender_id = user.id
            sender_room = f"user_{sender_id}"
            receiver_room = f"user_{receiver_id[0][1]}"
            # Save the chat message to the database
            chat = Chat(
                receiver_id=receiver_id[0][1],
                sender_id=user.id,
                parent_id=int(parent_id[0][1])
                if parent_id and parent_id[0][1].isdigit()
                else None,
            )

            # Check if file data is present
            if file_data:
                # Decode base64 encoded file data
                file_content = base64.b64decode(file_data)
                print("decode ", file_content)
                file_name = f"{uuid.uuid4().hex}.file"

                # Save the file content to the file_field
                await sync_to_async(chat.file_field.save)(
                    file_name, ContentFile(file_content), save=True
                )

            # Save the chat message to the database using sync_to_async
            await self.save_chat_to_database(chat)
            # Save the chat instance to the database
            # await self.save_chat_to_database(chat)

            # Broadcast the message to the sender and receiver
            await self.channel_layer.group_send(
                sender_room,
                {
                    "type": "chat.message",
                    "message": file_data,
                    "message_type": message_type,
                    "parent_id": parent_id[0][1],
                    "file_data": file_data,
                },
            )

            await self.channel_layer.group_send(
                receiver_room,
                {
                    "type": "chat.message",
                    "message": file_data,
                    "message_type": message_type,
                    "parent_id": parent_id[0][1],
                    "file_data": file_data,
                },
            )

    async def websocket_disconnect(self, event):
        auth_user, _ = self.user
        user = await database_sync_to_async(User.objects.get)(email=auth_user)
        user_id = user.id
        chat_room = f"user_{user_id}"
        print("Websocket Disconnected...")
        await self.channel_layer.group_discard(chat_room, self.channel_name)
        raise StopConsumer()

    async def chat_message(self, event):
        message_type = event.get("message_type", "")

        await self.send(
            {
                "type": "websocket.send",
                "text": json.dumps(
                    {"message": event["message"], "message_type": message_type}
                ),
            }
        )

    async def get_user(self):
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        token_param = [
            param.split("=")
            for param in query_string.split("&")
            if param.startswith("token=")
        ]

        token = token_param[0][1]
        decoded_user = await sync_to_async(JWTAuthentication.decode_token)(
            JWTAuthentication, token
        )
        return decoded_user

    @sync_to_async
    def save_chat_to_database(self, chat):
        chat.save()

    @database_sync_to_async
    def get_chat_object(self, chat_id):
        return Chat.objects.get(id=chat_id)

    @database_sync_to_async
    def get_user_object(self, user_id):
        return User.objects.get(id=user_id)
