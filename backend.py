import os
import sqlite3
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pypdf
# import docx
from dotenv import load_dotenv
load_dotenv()

# ---------------- Gemini API ----------------
api_key = os.getenv("GEMINI_API_KEY")
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=api_key)

# ---------------- SQLite Config ----------------
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpoint = SqliteSaver(conn)

# ---------------- Qdrant Config ----------------
COLLECTION_NAME = "student_docs"
qdrant = qdrant_client = QdrantClient(
        
    url="https://800fd5b9-5fe6-4658-8d6a-941a6fc4f549.eu-central-1-0.aws.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.7yz2MAIM9IRIkL3IrlNq9uQ4EfFMldC6S1JyQMNevYw",
)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------- Chat State ----------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ---------------- Helpers ----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in {"pdf","docx","txt"}

def extract_text(filepath):
    ext = filepath.split(".")[-1].lower()
    text = ""
    if ext == "pdf":
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    elif ext == "docx":
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif ext == "txt":
        with open(filepath,"r",encoding="utf-8") as f:
            text = f.read()
    return text.strip()

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n","\n",".","!","?"," "]
    )
    return splitter.split_text(text)

import uuid

def upload_to_qdrant(filepath):
    text = extract_text(filepath)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    vectors = embedder.encode(chunks).tolist()

    # Create collection if it doesn't exist
    try:
        qdrant.get_collection(COLLECTION_NAME)
    except:
        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE)
        )

    # Upload points
    points = []
    for i, chunk in enumerate(chunks):
        points.append(models.PointStruct(
            id=str(uuid.uuid4()),  # <-- use UUID instead of custom string
            vector=vectors[i],
            payload={
                "text": chunk,
                "source_file": os.path.basename(filepath),
                "chunk_id": i
            }
        ))
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(chunks)
    text = extract_text(filepath)
    chunks = chunk_text(text)
    if not chunks:
        return 0
    vectors = embedder.encode(chunks).tolist()

    # Create collection if not exists
    try:
        qdrant.get_collection(COLLECTION_NAME)
    except:
        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE)
        )

    # Upload points
    points = []
    for i, chunk in enumerate(chunks):
        points.append(models.PointStruct(
            id=str(i) + "_" + os.path.basename(filepath),
            vector=vectors[i],
            payload={"text": chunk,"source_file": os.path.basename(filepath),"chunk_id": i}
        ))
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(chunks)

# ---------------- Retrieve Context ----------------
def retrieve_context(query, top_k=3):
    vec = embedder.encode([query])[0].tolist()
    results = qdrant.search(collection_name=COLLECTION_NAME, query_vector=vec, limit=top_k)
    return [hit.payload["text"] for hit in results]

# ---------------- Chat Node ----------------
def chat_node(state: ChatState) -> ChatState:
    messages = state['messages']
    if not messages:
        return {"messages": []}
    last_msg = messages[-1].content

    # Retrieve context
    context_chunks = retrieve_context(last_msg)
    context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant context found."

    # Augmented prompt
    augmented_prompt = f"""
    You are a helpful assistant. Use the following context to answer the question.

    Context:
    {context_text}

    Question:
    {last_msg}

    If context is not enough, respond accordingly.
    """
    response = model.invoke([HumanMessage(content=augmented_prompt)])
    return {"messages":[response]}

# ---------------- State Graph ----------------
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)
chatbot = graph.compile(checkpointer=checkpoint)

# ---------------- Retrieve Threads ----------------
def retrive_all_threads():
    all_threads = set()
    for check in checkpoint.list(None):
        all_threads.add(check.config['configurable']['thread_id'])
    return list(all_threads)

# ---------------- Load Conversation ----------------
def load_con(thread_id):
    state = chatbot.get_state(config={"configurable":{"thread_id":thread_id}})
    values = state.values
    messages = values.get("messages",[])
    temp_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        temp_messages.append({"role":role,"content":msg.content})
    return temp_messages
