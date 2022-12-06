import logging
import os

from open_ai_chat import OpenAiChatClient

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)


class ChatBot:
    def __init__(self, client: OpenAiChatClient):
        self._client = client

    def run(self):
        conversation = {"conversation_id": None, "parent_message_id": ""}
        while True:
            prompt = input("You: ")
            response = self._client.conversation(
                prompt,
                conversation["conversation_id"],
                conversation["parent_message_id"],
            )
            conversation["conversation_id"] = response.conversation_id
            conversation["parent_message_id"] = response.message.id

            print("Bot:")
            print(response.text)


# Load from environment variables
OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")

client = OpenAiChatClient(OPENAI_SESSION_TOKEN)
chat_bot = ChatBot(client)
chat_bot.run()
