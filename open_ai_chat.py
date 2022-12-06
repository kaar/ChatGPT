import json
import logging
import os
import uuid
from dataclasses import dataclass

import requests

from cache import DbmCache

LOGGER = logging.getLogger(__name__)
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))


def generate_uuid():
    uid = str(uuid.uuid4())
    return uid


class OpenAiChatSession:
    def __init__(self, session_token: str):
        self.session_token = session_token
        self._cache = DbmCache(
            os.path.join(XDG_CACHE_HOME, "open_api_chat", "") + "session.db"
        )
        self._access_token = None

    @property
    def access_token(self) -> str:
        if not self._access_token:
            self._access_token = self._get_access_token()
        return self._access_token

    def refresh_access_token(self):
        self._access_token = None
        self._cache.drop("access_token")

    def _get_access_token(self):
        access_token = self._cache.get("access_token")
        if access_token:
            LOGGER.debug("Access token found in cache.")
            return access_token

        try:
            LOGGER.debug("Get access token...")
            session = requests.Session()
            session.cookies.set("__Secure-next-auth.session-token", self.session_token)
            response = session.get("https://chat.openai.com/api/auth/session")
            response.raise_for_status()
            access_token = response.json()["accessToken"]
            LOGGER.debug("Access token retrieved.")
            self._cache.set("access_token", access_token)
            return access_token
        except Exception as e:
            LOGGER.exception(e)
            raise


@dataclass
class Conversation:
    name: str
    id: str | None = None
    parent_id: str = generate_uuid()


@dataclass
class Content:
    content_type: str
    parts: list[str]


@dataclass
class Message:
    id: str
    role: str
    user: str | None
    create_time: str | None
    update_time: str | None
    content: Content
    end_turn: str | None
    weight: float
    metadata: dict
    recipient: str


@dataclass
class ConversationResponse:
    message: Message
    conversation_id: str
    error: str

    @property
    def text(self) -> str:
        return self.message.content.parts[0]


class OpenAiChatClient:
    def __init__(self, session: OpenAiChatSession):
        self.session = session

    def conversation(
        self, conversation: Conversation, prompt: str
    ) -> ConversationResponse:
        data = {
            "action": "next",
            "messages": [
                {
                    "id": str(generate_uuid()),
                    "role": "user",
                    "content": {"content_type": "text", "parts": [prompt]},
                }
            ],
            "conversation_id": conversation.id,
            "parent_message_id": conversation.parent_id,
            "model": "text-davinci-002-render",
        }
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.session.access_token,
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://chat.openai.com/backend-api/conversation",
            headers=headers,
            data=json.dumps(data),
        )
        # Unauthorized
        if response.status_code == 401:
            self.session.refresh_access_token()

        try:
            # data: {
            #     "message": {
            #         "id": "09bdd77f-8195-4cbf-9bfa-0c6d0e992c6a",
            #         "role": "assistant",
            #         "user": null,
            #         "create_time": null,
            #         "update_time": null,
            #         "content": {
            #             "content_type": "text",
            #             "parts": [
            #                 "Hello again! Is there anything specific you would like to discuss or ask about? I'm here to help with any questions you have. Let me know if you need any assistance."
            #             ],
            #         },
            #         "end_turn": null,
            #         "weight": 1.0,
            #         "metadata": {},
            #         "recipient": "all",
            #     },
            #     "conversation_id": "4e508ea6-1794-4d43-85e3-91210cce8f15",
            #     "error": null,
            # }
            response = response.text.splitlines()[-4]
            resp = json.loads(response[6:])
            msg = resp["message"]
            return ConversationResponse(
                message=Message(
                    id=msg["id"],
                    role=msg["role"],
                    user=msg["user"],
                    create_time=msg["create_time"],
                    update_time=msg["update_time"],
                    content=Content(
                        content_type=msg["content"]["content_type"],
                        parts=msg["content"]["parts"],
                    ),
                    end_turn=msg["end_turn"],
                    weight=msg["weight"],
                    metadata=msg["metadata"],
                    recipient=msg["recipient"],
                ),
                conversation_id=resp["conversation_id"],
                error=resp["error"],
            )
        except:
            raise
        # data = json.loads(response)
        # return Message(
        #     conversation_id=data["conversation_id"],
        #     parent_id=data["message"]["id"],
        #     text=data["message"]["content"]["parts"][0],
        # )
