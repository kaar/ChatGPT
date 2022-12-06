import json
import logging
import os
import uuid
from dataclasses import dataclass

import requests

LOGGER = logging.getLogger(__name__)
XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))


def generate_uuid():
    uid = str(uuid.uuid4())
    return uid


@dataclass
class Conversation:
    name: str
    id: str | None = None
    parent_message_id: str = generate_uuid()


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
    def __init__(self, session_token: str):
        self.session_token = session_token
        self._access_token = None

    def _get_access_token(self):
        try:
            LOGGER.debug("Get access token...")
            session = requests.Session()
            session.cookies.set("__Secure-next-auth.session-token", self.session_token)
            response = session.get("https://chat.openai.com/api/auth/session")
            response.raise_for_status()
            access_token = response.json()["accessToken"]
            LOGGER.debug("Access token retrieved.")
            return access_token
        except Exception as e:
            LOGGER.exception(e)
            raise

    @property
    def access_token(self):
        if not self._access_token:
            self._access_token = self._get_access_token()
        return self._access_token

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
            "parent_message_id": conversation.parent_message_id,
            "model": "text-davinci-002-render",
        }
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://chat.openai.com/backend-api/conversation",
            headers=headers,
            data=json.dumps(data),
        )
        # Unauthorized
        if response.status_code == 401:
            self._access_token = None
            # TODO: retry
            raise ValueError("Unauthorized")

        data = json.loads(response.text.splitlines()[-4][6:])
        msg = data["message"]
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
            conversation_id=data["conversation_id"],
            error=data["error"],
        )
