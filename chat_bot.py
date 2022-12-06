import json
import logging
import os

from cache import DbmCache
from open_ai_chat import OpenAiChatClient

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)


XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))


class ConversationStore:
    def __init__(self):
        self._cache = DbmCache(
            os.path.join(XDG_CACHE_HOME, "chatbot", "") + "conversations.db"
        )

    def get(self, name, default=None):
        data = self._cache.get(name)
        if not data:
            LOGGER.debug("Creating new conversation with name: '%s'", name)
            return default

        return data

    def save(self, name: str, data: dict):
        self._cache.set(name, data)

    def list(self):
        return self._cache.list()


class ChatBot:
    def __init__(self, client: OpenAiChatClient, conversation_name: str = "default"):
        self._client = client
        self._conversation_store = ConversationStore()
        self.conversation_name = conversation_name

    def run(self):
        conversation = self._conversation_store.get(
            self.conversation_name,
            default={"conversation_id": None, "parent_message_id": ""},
        )
        while True:
            prompt = input("You: ")
            response = self._client.conversation(
                prompt,
                conversation["conversation_id"],
                conversation["parent_message_id"],
            )
            conversation["conversation_id"] = response.conversation_id
            conversation["parent_message_id"] = response.message.id

            self._conversation_store.save(self.conversation_name, conversation)

            print("Bot:")
            print(response.text)


# Load from environment variables
OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")

client = OpenAiChatClient(OPENAI_SESSION_TOKEN)
chat_bot = ChatBot(client, conversation_name="default")
chat_bot.run()
