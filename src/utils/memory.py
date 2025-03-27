from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.schema.messages import AIMessage, HumanMessage

# Global memory instance
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def add_user_message(text):
    memory.chat_memory.add_user_message(text)

def add_ai_message(text):
    memory.chat_memory.add_ai_message(text)

def get_memory_messages():
    return memory.chat_memory.messages
