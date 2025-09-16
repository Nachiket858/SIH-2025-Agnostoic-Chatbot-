# utilities.py
import os
import uuid
from flask import session
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pypdf
import docx
import traceback

# ---------------- Hardcoded Qdrant Config ----------------
COLLECTION_NAME = "student_docs"
QDRANT_URL = "https://24062022-271d-4916-949c-8b99152d7ddf.eu-central-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.cW3MmgsORw1ICQqwsb1C1U6EzRY5o8k1SYp2xorh0Uw"

# Initialize Qdrant client
try:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    _ = qdrant.get_collections()  # sanity check
except Exception as e:
    print("Warning: Qdrant initialization failed.", e)
    qdrant = None

# ---------------- Embedder ----------------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------- Session helpers ----------------
def generate_thread_id():
    return str(uuid.uuid4())

def add_thread(thread_id):
    if "chat_threads" not in session:
        session["chat_threads"] = []
    if thread_id not in session["chat_threads"]:
        session["chat_threads"].append(thread_id)

# ---------------- File helpers ----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf", "docx", "txt"}

def extract_text(filepath: str) -> str:
    ext = filepath.split(".")[-1].lower()
    text = ""
    if ext == "pdf":
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                text += txt + "\n"
    elif ext == "docx":
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
    elif ext == "txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    return text.strip()

def chunk_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", " "],
    )
    return splitter.split_text(text)

# ---------------- Qdrant upload ----------------
def upload_to_qdrant(filepath):
    if qdrant is None:
        print("Qdrant not available, skipping upload")
        return 0

    text = extract_text(filepath)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    vectors = embedder.encode(chunks).tolist()

    try:
        qdrant.get_collection(COLLECTION_NAME)
    except Exception:
        try:
            qdrant.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=len(vectors[0]), distance=models.Distance.COSINE
                ),
            )
        except Exception as e:
            print(f"Qdrant upload failed: {e}")
            return 0

    points = []
    for i, chunk in enumerate(chunks):
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i],
                payload={
                    "text": chunk,
                    "source_file": os.path.basename(filepath),
                    "chunk_id": i,
                },
            )
        )
    try:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    except Exception as e:
        print(f"Qdrant upload failed during upsert: {e}")
        return 0

    return len(chunks)

# ---------------- Retrieve context ----------------
def retrieve_context(query: str, top_k: int = 3):
    if qdrant is None:
        return []

    try:
        vec = embedder.encode([query])[0].tolist()
        results = qdrant.search(collection_name=COLLECTION_NAME, query_vector=vec, limit=top_k)
        return [hit.payload.get("text", "") for hit in results]
    except Exception as e:
        print("Qdrant search/retrieve_context failed:", e)
        traceback.print_exc()
        return []
