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


class OpenApiSession:
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


class ChatBot:
    def __init__(self, session: OpenApiSession, conversation: Conversation):
        self.session = session
        self.conversation = conversation
        self._conversation_store = ConversationStore()

    def get_chat_response(self, prompt) -> dict:
        data = {
            "action": "next",
            "messages": [
                {
                    "id": str(generate_uuid()),
                    "role": "user",
                    "content": {"content_type": "text", "parts": [prompt]},
                }
            ],
            "conversation_id": self.conversation.id,
            "parent_message_id": self.conversation.parent_id,
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
        response = json.loads(response)
        self.conversation.parent_id = response["message"]["id"]
        self.conversation.id = response["conversation_id"]
        message = response["message"]["content"]["parts"][0]
        message = {
            "message": message,
            "conversation_id": self.conversation.id,
            "parent_id": self.conversation.parent_id,
        }
        self._conversation_store.save(self.conversation)
        return message


# Load from environment variables
OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")


# load_conversation = cache_get("conversation")
# if load_conversation:

conv_store = ConversationStore()
conversations = conv_store.list()

print(f"Conversations: {len(conversations)}")
for c in conversations:
    print(c)

# conv_store.clear()
# exit()

conversation = conv_store.get("test")
session = OpenApiSession(OPENAI_SESSION_TOKEN)
cb = ChatBot(session, conversation=conversation)
while True:
    prompt = input("You: ")
    resp = cb.get_chat_response(prompt)
    print("Bot:")
    print(resp["message"])
