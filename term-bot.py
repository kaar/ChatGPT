import json
import logging
import os
import uuid

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_uuid():
    uid = str(uuid.uuid4())
    return uid


def get_access_token(session_token: str):
    LOGGER.debug("Getting access token...")
    try:
        session = requests.Session()
        session.cookies.set("__Secure-next-auth.session-token", session_token)
        response = session.get("https://chat.openai.com/api/auth/session")
        response.raise_for_status()

        access_token = response.json()["accessToken"]
        LOGGER.debug("Access token: ", access_token)
        return access_token
    except Exception as e:
        LOGGER.exception(e)
        raise


class ChatBot:
    def __init__(self, session_token):
        self.session_token = session_token
        self.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + get_access_token(session_token),
            "Content-Type": "application/json",
        }
        self.conversation_id = None
        self.parent_id = generate_uuid()

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
            "conversation_id": self.conversation_id,
            "parent_message_id": self.parent_id,
            "model": "text-davinci-002-render",
        }
        response = requests.post(
            "https://chat.openai.com/backend-api/conversation",
            headers=self.headers,
            data=json.dumps(data),
        )
        # json_data = response.json()
        # print(f"json_data: {json_data}")
        try:
            response = response.text.splitlines()[-4]
            response = response[6:]
        except:
            raise
        response = json.loads(response)
        self.parent_id = response["message"]["id"]
        self.conversation_id = response["conversation_id"]
        message = response["message"]["content"]["parts"][0]
        return {
            "message": message,
            "conversation_id": self.conversation_id,
            "parent_id": self.parent_id,
        }


# Load from environment variables
OPENAI_SESSION_TOKEN = os.environ["OPENAI_SESSION_TOKEN"]

if not OPENAI_SESSION_TOKEN:
    raise ValueError("Missing OPENAI_SESSION_TOKEN")


cb = ChatBot(OPENAI_SESSION_TOKEN)

while True:
    prompt = input("You: ")
    resp = cb.get_chat_response(prompt)
    print("Bot:")
    print(resp["message"])
