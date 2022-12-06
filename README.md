# Term Bot
ChatGPT terminal bot

## Example

```
$ echo "Write something fun about abstract functions in Python" | ./chat.py

An abstract function in Python is like a superhero with a secret
identity. From the outside, it looks just like a normal function, but
it has special powers that allow it to perform incredible feats. For
example, an abstract function can override other functions and control
their behavior, or it can even define new behavior for a whole class of
objects. But just like a superhero, an abstract function can only use
its powers for good – it must be implemented by a concrete subclass
before it can be called, so that it can help solve real-world problems
and make the world a better place.
```

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
