import logging
import os

from open_ai_chat import OpenAiChatClient

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)

OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")

client = OpenAiChatClient(OPENAI_SESSION_TOKEN)

conversation = {"conversation_id": None, "parent_message_id": ""}

while True:
    prompt = input("You: ")
    response = client.conversation(
        prompt,
        conversation["conversation_id"],
        conversation["parent_message_id"],
    )
    conversation["conversation_id"] = response.conversation_id
    conversation["parent_message_id"] = response.message.id

    print("Bot:")
    print(response.text)
