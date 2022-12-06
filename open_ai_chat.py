import json
import logging
import uuid
from dataclasses import dataclass

import requests

LOGGER = logging.getLogger(__name__)


def generate_uuid():
    uid = str(uuid.uuid4())
    return uid


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

    def conversation(
        self,
        prompt: str,
        conversation_id: str | None = None,
        parent_message_id: str = "",
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
            "conversation_id": conversation_id,
            "parent_message_id": parent_message_id or str(generate_uuid()),
            "model": "text-davinci-002-render",
        }

        MAX_RETRIES = 3
        for retry in range(MAX_RETRIES):
            try:
                headers = {
                    "Accept": "application/json",
                    "Authorization": "Bearer " + self.access_token(),
                    "Content-Type": "application/json",
                }
                response = requests.post(
                    "https://chat.openai.com/backend-api/conversation",
                    headers=headers,
                    data=json.dumps(data),
                )

                if response.status_code == 401:
                    LOGGER.debug("Access token expired. Refreshing...")
                    self._access_token = None

                response.raise_for_status()

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
            except requests.exceptions.RequestException as e:
                LOGGER.warning(
                    f"Request failed. Retrying... ({retry + 1}/{MAX_RETRIES})"
                )
                if retry == MAX_RETRIES - 1:
                    raise e

        raise RuntimeError("Should not reach here")

    def access_token(self):
        if not self._access_token:
            self._access_token = self._get_access_token()
        return self._access_token

    def _get_access_token(self):
        try:
            session = requests.Session()
            session.cookies.set("__Secure-next-auth.session-token", self.session_token)
            response = session.get("https://chat.openai.com/api/auth/session")
            response.raise_for_status()
            return response.json()["accessToken"]
        except requests.exceptions.RequestException as e:
            LOGGER.exception(e)
            raise
