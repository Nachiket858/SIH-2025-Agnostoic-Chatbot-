# utilities.py
import os
import uuid
import traceback

from flask import session
from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.http import models

from langchain_text_splitters import RecursiveCharacterTextSplitter

import pypdf
import docx

# ----------------------------------------------------
# Qdrant Configuration
# ----------------------------------------------------
COLLECTION_NAME = "student_docs"
QDRANT_URL = "https://30379eb1-d7db-44ac-9838-c8b759fae2c6.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.pAaS4hvrmqlhnGQmmmpotowiHFPLPBSIaX1rfRTibeI"

# Initialize Qdrant client
try:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    _ = qdrant.get_collections()
except Exception as e:
    print("Warning: Qdrant initialization failed.", e)
    qdrant = None

# ----------------------------------------------------
# Embedding Model
# ----------------------------------------------------
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# ----------------------------------------------------
# Session Helpers
# ----------------------------------------------------
def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if "chat_threads" not in session:
        session["chat_threads"] = []
    if thread_id not in session["chat_threads"]:
        session["chat_threads"].append(thread_id)


# ----------------------------------------------------
# File Handling
# ----------------------------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf", "docx", "txt"}


def extract_text(filepath: str) -> str:
    ext = filepath.lower().split(".")[-1]
    text = ""

    if ext == "pdf":
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    elif ext == "docx":
        doc_file = docx.Document(filepath)
        for para in doc_file.paragraphs:
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


# ----------------------------------------------------
# Upload to Qdrant
# ----------------------------------------------------
def upload_to_qdrant(filepath):
    """
    Extract text, chunk it, embed it, and upload to Qdrant using new API.
    """
    if qdrant is None:
        print("Qdrant unavailable. Skipping upload.")
        return 0

    text = extract_text(filepath)
    chunks = chunk_text(text)

    if not chunks:
        return 0

    vectors = embedder.encode(chunks).tolist()
    vector_size = len(vectors[0])

    # Create collection if needed
    try:
        qdrant.get_collection(COLLECTION_NAME)
    except Exception:
        try:
            qdrant.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
        except Exception as e:
            print("Failed to create Qdrant collection:", e)
            return 0

    # Prepare points
    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vectors[i],
            payload={
                "text": chunks[i],
                "source_file": os.path.basename(filepath),
                "chunk_id": i,
            },
        )
        for i in range(len(chunks))
    ]

    # Upload using new API: upload_points()
    try:
        qdrant.upload_points(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True
        )
    except Exception as e:
        print("Qdrant upload failed:", e)
        return 0

    return len(chunks)


# ----------------------------------------------------
# Retrieve Relevant Context
# ----------------------------------------------------
def retrieve_context(query: str, top_k: int = 3):
    if qdrant is None:
        return []

    try:
        query_vec = embedder.encode(query).tolist()

        # NEW search method → query_points()
        response = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vec,
            limit=top_k,
        )

        if not response.points:
            return []

        return [point.payload.get("text", "") for point in response.points]

    except Exception as e:
        print("Qdrant search/retrieve_context failed:", e)
        traceback.print_exc()
        return []

