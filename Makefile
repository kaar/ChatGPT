export OPENAI_SESSION_TOKEN := <OPENAI_SESSION_TOKEN>

chat:
	@python chat.py

ask:
	@python ash.py

.PHONY: run chat
