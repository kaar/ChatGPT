import json

import requests
from revChatGPT.revChatGPT import Chatbot

# Get your config in JSON
config = {
    "Authorization": "<Your Bearer Token Here>",  # This is optional
    "session_token": "<Your Session Token here>",  # This is used to refresh the authentication
}
prompt = "Hello"

chatbot = Chatbot(config, conversation_id=None)
chatbot.reset_chat()  # Forgets conversation
chatbot.refresh_session()  # Uses the session_token to get a new bearer token
resp = chatbot.get_chat_response(
    prompt, output="text"
)  # Sends a request to the API and returns the response by OpenAI
resp["message"]  # The message sent by the response
resp["conversation_id"]  # The current conversation id
resp["parent_id"]  # The ID of the response

print(resp)

response = requests.post(
    "https://chat.openai.com/backend-api/conversation",
    headers=self.headers,
    data=json.dumps(data),
    stream=True,
)  # This returns a stream of text (live update)

for message in response:  # You have to loop through the response stream
    print(line["message"])  # Same format as text return type
    ...
