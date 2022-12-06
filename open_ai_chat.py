import json
import logging
import uuid
from dataclasses import dataclass
from functools import wraps

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


def request_retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        MAX_ATTEMPTS = 3
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                if attempt == MAX_ATTEMPTS:
                    raise e
                LOGGER.warning(f"Attempt {attempt}/{MAX_ATTEMPTS} failed. Retrying...")

    return wrapper


class OpenAiChatClient:
    def __init__(self, session_token: str):
        self.session_token = session_token
        self._access_token = None

    @request_retry
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
            self._refresh_access_token()

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

    def access_token(self):
        if not self._access_token:
            self._refresh_access_token()

        return self._access_token

    def _refresh_access_token(self):
        try:
            session = requests.Session()
            session.cookies.set("__Secure-next-auth.session-token", self.session_token)
            response = session.get("https://chat.openai.com/api/auth/session")
            response.raise_for_status()
            self._access_token = response.json()["accessToken"]
        except requests.exceptions.RequestException as e:
            LOGGER.exception(e)
            raise
