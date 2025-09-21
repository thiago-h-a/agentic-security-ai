from langchain.memory import ConversationBufferMemory

# Shared memory object (expand later)
memory = ConversationBufferMemory(memory_key="history", return_messages=True)
