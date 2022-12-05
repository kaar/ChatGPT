# Term Bot
ChatGPT terminal bot


## Getting started
* How to get session_token
* Example

```python
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
```
