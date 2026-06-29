"""
Shared document processing for the async RAG pipeline.

Loaded once per worker process. Heavy resources (embedding model,
ChromaDB client) are module-level singletons so they are not
re-initialized on every message.
"""

from __future__ import annotations

import time
from functools import lru_cache

import chromadb
import fitz
import pytesseract
from docx import Document
from PIL import Image
from sentence_transformers import SentenceTransformer


from app.config import settings

COLLECTION_NAME = "smarthub_docs"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"




# ── Singletons (expensive — load once) ───────────────────────────────────────

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


@lru_cache(maxsize=1)
def get_chroma_collection():
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def _configure_tesseract() -> None:
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


_configure_tesseract()


# ── Extraction ───────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    try:
        return "".join(page.get_text() for page in doc)
    finally:
        doc.close()


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def extract_text_from_image(file_path: str) -> str:
    with Image.open(file_path) as image:
        return pytesseract.image_to_string(image)


def extract_text(file_path: str, filename: str) -> str:
    """Route to the correct extractor based on file extension."""
    extension = filename.rsplit(".", 1)[-1].lower()

    extractors = {
        "pdf": extract_text_from_pdf,
        "docx": extract_text_from_docx,
        "txt": extract_text_from_txt,
        "png": extract_text_from_image,
        "jpg": extract_text_from_image,
        "jpeg": extract_text_from_image,
    }

    extractor = extractors.get(extension)
    if extractor is None:
        raise ValueError(f"Unsupported file type: {extension}")

    return extractor(file_path)


# ── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Split text into word-based chunks (matches hub_ai behavior)."""
    words = text.split()
    if not words:
        return []

    return [
        " ".join(words[i : i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]


# ── Embedding ────────────────────────────────────────────────────────────────

def encode_text(text: str) -> list[float]:
    """Generate embedding vector for a single chunk."""
    model = get_embedding_model()
    return model.encode(text).tolist()


# ── Vector indexing ──────────────────────────────────────────────────────────

def index_chunk(
    *,
    filename: str,
    chunk_index: int,
    chunk_text: str,
    embedding: list[float],
    document_id: str,
    uploaded_at: float | None = None,
) -> str:
    """
    Store one chunk in ChromaDB. Returns the chunk ID used.

    ID format matches hub_ai: {filename}_chunk_{index}
    so query/delete logic in hub_ai keeps working.
    """
    collection = get_chroma_collection()
    chunk_id = f"{filename}_chunk_{chunk_index}"

    collection.add(
        documents=[chunk_text],
        embeddings=[embedding],
        ids=[chunk_id],
        metadatas=[{
            "filename": filename,
            "document_id": document_id,
            "uploaded_at": uploaded_at or time.time(),
        }],
    )

    return chunk_id