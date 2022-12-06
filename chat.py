#!/usr/bin/env python3

import logging
import os

from open_ai_chat import Conversation, OpenApiChatSession, OpenApiClient

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)


# Load from environment variables
OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")

session = OpenApiChatSession(OPENAI_SESSION_TOKEN)
client = OpenApiClient(session)


message = client.conversation(Conversation("chat"), input())

print(message.text)
