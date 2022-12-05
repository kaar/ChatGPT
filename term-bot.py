import dbm
import json
import logging
import os
import uuid
from dataclasses import dataclass

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))


class DbmCache:
    def __init__(self, cache_file: str):

        if not os.path.exists(cache_file):
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        self.cache_file = cache_file

    def get(self, key: str):
        with dbm.open(self.cache_file, "c") as db:
            if key in db:
                return json.loads(db[key])
        return None

    def set(self, key: str, value: dict):
        with dbm.open(self.cache_file, "c") as db:
            db[key] = json.dumps(value)

    def drop(self, key: str):
        with dbm.open(self.cache_file, "c") as db:
            if key in db:
                del db[key]

    def list(self):
        with dbm.open(self.cache_file, "c") as db:
            return list(db.keys())


def generate_uuid():
    uid = str(uuid.uuid4())
    return uid


@dataclass
class Conversation:
    name: str
    id: str | None = None
    parent_id: str = generate_uuid()


class ConversationStore:
    def __init__(self):
        self._cache = DbmCache(
            os.path.join(XDG_CACHE_HOME, "chatbot", "") + "conversations.db"
        )

    def get(self, name) -> Conversation:
        data = self._cache.get(name)
        if not data:
            LOGGER.debug("Creating new conversation with name: '%s'", name)
            return Conversation(name)

        conversation = Conversation(**data)
        LOGGER.debug(f"Loaded conversation from cache:\n{json.dumps(data, indent=1)}")
        return conversation

    def save(self, conversation: Conversation):
        LOGGER.debug(
            f"Saving conversation to cache:\n{json.dumps(conversation.__dict__, indent=1)}"
        )
        self._cache.set(conversation.name, conversation.__dict__)

    def list(self):
        return self._cache.list()


def get_access_token(session_token: str):
    try:
        LOGGER.debug("Get access token...")
        session = requests.Session()
        session.cookies.set("__Secure-next-auth.session-token", session_token)
        response = session.get("https://chat.openai.com/api/auth/session")
        response.raise_for_status()
        access_token = response.json()["accessToken"]
        return access_token
    except Exception as e:
        LOGGER.exception(e)
        raise


class OpenApiChatSession:
    def __init__(self, session_token: str):
        self.session_token = session_token
        self._cache = DbmCache(
            os.path.join(XDG_CACHE_HOME, "chatbot", "") + "session.db"
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


class ChatBot:
    def __init__(self, client: OpenApiClient, conversation_name: str = "default"):
        self._client = client
        self._conversation_store = ConversationStore()
        self.conversation_name = conversation_name

    def run(self):
        while True:
            conversation = self._conversation_store.get(self.conversation_name)

            prompt = input("You: ")
            message = self._client.conversation(conversation, prompt)
            # update conversation

            conversation.id = message.conversation_id
            conversation.parent_id = message.parent_id

            self._conversation_store.save(conversation)

            print("Bot:")
            print(message.text)


# Load from environment variables
OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")


session = OpenApiChatSession(OPENAI_SESSION_TOKEN)
client = OpenApiClient(session)

chat_bot = ChatBot(client, conversation_name="default")
chat_bot.run()
