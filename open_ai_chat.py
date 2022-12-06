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


class OpenApiChatSession:
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
class Message:
    conversation_id: str
    parent_id: str
    text: str


class OpenApiClient:
    def __init__(self, session: OpenApiChatSession):
        self.session = session

    def conversation(self, conversation: Conversation, prompt: str) -> Message:
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
            response = response.text.splitlines()[-4]
            response = response[6:]
        except:
            raise
        data = json.loads(response)
        return Message(
            conversation_id=data["conversation_id"],
            parent_id=data["message"]["id"],
            text=data["message"]["content"]["parts"][0],
        )
