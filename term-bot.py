import dbm
import json
import logging
import os
import uuid
from dataclasses import dataclass

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
LOGGER.debug("Starting up")


XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
CACHE_FILE = os.path.join(XDG_CACHE_HOME, "chatbot", "") + "cache.db"
if not os.path.exists(CACHE_FILE):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)


def cache_get(key: str):
    with dbm.open(CACHE_FILE, "c") as db:
        if key in db:
            return json.loads(db[key])
    return None


def cache_set(key: str, value: dict):
    with dbm.open(CACHE_FILE, "c") as db:
        db[key] = json.dumps(value)


def generate_uuid():
    uid = str(uuid.uuid4())
    return uid


def get_access_token(session_token: str):
    LOGGER.debug("Getting access token...")

    access_token = cache_get("access_token")
    if access_token:
        LOGGER.debug("Got access token from cache")
        return access_token

    try:
        session = requests.Session()
        session.cookies.set("__Secure-next-auth.session-token", session_token)
        response = session.get("https://chat.openai.com/api/auth/session")
        response.raise_for_status()

        access_token = response.json()["accessToken"]
        LOGGER.debug("Access token: ", access_token)
        cache_set("access_token", access_token)
        return access_token
    except Exception as e:
        LOGGER.exception(e)
        raise


@dataclass
class Conversation:
    name: str
    id: str | None = None
    parent_id: str = generate_uuid()


def get_conversation(name) -> Conversation:
    data = cache_get(name)
    if not data:
        LOGGER.debug("Creating new conversation")
        return Conversation(name)

    conversation = Conversation(**data)
    LOGGER.debug(f"Loaded conversation from cache:\n{json.dumps(data, indent=1)}")
    return conversation


def save_conversation(conversation: Conversation):
    LOGGER.debug(
        f"Saving conversation to cache. id: {conversation.id}, parent_id: {conversation.parent_id}"
    )
    cache_set(conversation.name, conversation.__dict__)


class ChatBot:
    def __init__(self, session_token, conversation_name: str):
        self.session_token = session_token
        self.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + get_access_token(session_token),
            "Content-Type": "application/json",
        }
        self.conversation: Conversation = get_conversation(conversation_name)

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
        response = requests.post(
            "https://chat.openai.com/backend-api/conversation",
            headers=self.headers,
            data=json.dumps(data),
        )
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
        save_conversation(self.conversation)
        cache_set("conversation", message)
        return message


# Load from environment variables
OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")


# load_conversation = cache_get("conversation")
# if load_conversation:

cb = ChatBot(OPENAI_SESSION_TOKEN, conversation_name="test")
while True:
    prompt = input("You: ")
    resp = cb.get_chat_response(prompt)
    print("Bot:")
    print(resp["message"])
