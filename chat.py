#!/usr/bin/env python3

import logging
import os

from open_ai_chat import Conversation, OpenAiChatClient, OpenAiChatSession

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)


OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")

session = OpenAiChatSession(OPENAI_SESSION_TOKEN)
client = OpenAiChatClient(session)


message = client.conversation(Conversation("chat"), input())

print(message.text)
