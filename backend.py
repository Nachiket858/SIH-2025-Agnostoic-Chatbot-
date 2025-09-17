# backend.py
import os
import sqlite3
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from utilities import retrieve_context  # uses embedder/qdrant
import traceback

load_dotenv()

# ---------------- Gemini API ----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not set. Model will likely fail at runtime.")
model = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                              api_key=GEMINI_API_KEY)

# ---------------- SQLite Config (checkpoint) ----------------
conn = sqlite3.connect(os.getenv("CHAT_DB", "chatbot.db"), check_same_thread=False)
checkpoint = SqliteSaver(conn)

# ---------------- Chat State Type ----------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ---------------- Chat Node ----------------
def chat_node(state: ChatState) -> ChatState:
    """
    Receives the current state's messages (list of BaseMessage).
    It appends the assistant response (from Gemini) to the messages list and returns the new state.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}

    # Last user message content
    last_msg = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

    # retrieve relevant chunks from Qdrant (may return empty list)
    try:
        context_chunks = retrieve_context(last_msg)
    except Exception:
        context_chunks = []
        traceback.print_exc()

    context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant context found."

    from langchain_core.messages import SystemMessage

    # Build messages list for model: system message with context + all previous messages
    system_message = SystemMessage(content=f"You are a helpful college  assistant. Use the following context to answer the question.\n\nContext:\n{context_text}\n\nIf context is not enough, respond accordingly.")

    # Pass all previous messages (including user and assistant) to the model
    # messages is a list of BaseMessage, so we can pass as is after prepending system_message
    model_messages = [system_message] + messages

    # Call the underlying generative model
    try:
        assistant_message = model.invoke(model_messages)
    except Exception as e:
        print("Model invocation failed:", e)
        traceback.print_exc()
        # If model fails, return state unchanged (or optionally append an error assistant msg)
        # We'll append a safe assistant message so UI shows something
        from langchain_core.messages import BaseMessage
        class SimpleAssistant(BaseMessage):
            def __init__(self, content):
                self.content = content
        assistant_message = SimpleAssistant("Sorry, I'm currently unable to generate a response.")

    # Append assistant response (preserve previous messages)
    new_messages = messages + [assistant_message]
    return {"messages": new_messages}

# ---------------- State Graph ----------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)
chatbot = graph.compile(checkpointer=checkpoint)

# ---------------- Threads (persistence helpers) ----------------
def retrive_all_threads():
    all_threads = set()
    try:
        for check in checkpoint.list(None):
            cfg = check.config
            if cfg and "configurable" in cfg and "thread_id" in cfg["configurable"]:
                all_threads.add(cfg["configurable"]["thread_id"])
    except Exception:
        traceback.print_exc()
    return list(all_threads)

def load_con(thread_id):
    try:
        state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
        values = state.values
        messages = values.get("messages", [])
        temp_messages = []
        # Map BaseMessage objects to dicts for the UI
        for msg in messages:
            # HumanMessage => user; otherwise assistant
            from langchain_core.messages import HumanMessage as LHHuman
            role = "user" if isinstance(msg, LHHuman) else "assistant"
            content = getattr(msg, "content", str(msg))
            temp_messages.append({"role": role, "content": content})
        return temp_messages
    except Exception:
        traceback.print_exc()
        return []
