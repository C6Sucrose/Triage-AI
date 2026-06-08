"""RAG ingestion and retrieval engine for Triage AI.

Provides three public functions:

- ``ingest_document`` – splits raw text into chunks, embeds them with a
  local HuggingFace model, and stores the resulting vectors in a ChromaDB
  collection with tenant-scoped metadata.
- ``retrieve_context`` – performs a similarity search against ChromaDB,
  filtered by ``tenant_id``, and returns concatenated page content from the
  top-k matched chunks for use by the drafter node.
- ``test_retrieval`` – performs a single-chunk similarity search for
  quick validation / debugging.
"""

import logging
import os

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("triage.backend.rag_engine")

_COLLECTION_NAME: str = "triage_kb"

_EMBEDDING_MODEL: HuggingFaceEmbeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
)

_TEXT_SPLITTER: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)


def _chroma_client() -> chromadb.HttpClient:
    url: str = os.getenv("CHROMA_DB_URL", "")
    if not url:
        raise EnvironmentError("CHROMA_DB_URL is not set in the environment")
    return chromadb.HttpClient(host=url)


def ingest_document(text: str, tenant_id: str, filename: str) -> int:
    """Chunk, embed, and persist a document into the ChromaDB vector store.

    Args:
        text: The full extracted text of a document (e.g. from
            ``extract_text_from_pdf``).
        tenant_id: Identifier of the tenant that owns this document.  Stored
            as chunk metadata to enforce data isolation at retrieval time.
        filename: Original filename of the source document, stored as chunk
            metadata for traceability.

    Returns:
        The number of chunks that were created and inserted.

    Raises:
        EnvironmentError: If ``CHROMA_DB_URL`` is not configured.
    """
    if not text.strip():
        logger.warning("Empty text received for ingestion — nothing to store")
        return 0

    chunks: list[str] = _TEXT_SPLITTER.split_text(text)
    metadatas: list[dict[str, str]] = [
        {"tenant_id": tenant_id, "filename": filename}
        for _ in chunks
    ]

    Chroma.from_texts(
        texts=chunks,
        embedding=_EMBEDDING_MODEL,
        metadatas=metadatas,
        collection_name=_COLLECTION_NAME,
        client=_chroma_client(),
    )

    logger.info(
        "Ingested %d chunks for tenant=%s, file=%s",
        len(chunks),
        tenant_id,
        filename,
    )
    return len(chunks)


def retrieve_context(query: str, tenant_id: str, k: int = 3) -> str:
    """Retrieve the top-k most relevant chunks for a query, scoped to a tenant.

    Args:
        query: The natural-language search query.
        tenant_id: Tenant identifier used as a ChromaDB metadata filter to
            guarantee data isolation between tenants.
        k: Number of top chunks to retrieve. Defaults to 3.

    Returns:
        The concatenated page content of all matched chunks, separated by
        double newlines.  Returns an empty string when no results are found.

    Raises:
        EnvironmentError: If ``CHROMA_DB_URL`` is not configured.
    """
    vectorstore: Chroma = Chroma(
        collection_name=_COLLECTION_NAME,
        embedding_function=_EMBEDDING_MODEL,
        client=_chroma_client(),
    )

    results: list[Document] = vectorstore.similarity_search(
        query=query,
        k=k,
        filter={"tenant_id": tenant_id},
    )

    if not results:
        logger.warning(
            "No retrieval results for query='%s', tenant=%s",
            query,
            tenant_id,
        )
        return ""

    context: str = "\n\n".join(doc.page_content for doc in results)
    logger.info(
        "Retrieved %d chunks for query='%s', tenant=%s — total length=%d",
        len(results),
        query,
        tenant_id,
        len(context),
    )
    return context


def test_retrieval(query: str, tenant_id: str) -> str:
    """Retrieve the most relevant chunk for a query, scoped to a tenant.

    Args:
        query: The natural-language search query.
        tenant_id: Tenant identifier used as a ChromaDB metadata filter to
            guarantee data isolation between tenants.

    Returns:
        The text content of the top-ranked matching chunk.  Returns an empty
        string when no results are found.

    Raises:
        EnvironmentError: If ``CHROMA_DB_URL`` is not configured.
    """
    vectorstore: Chroma = Chroma(
        collection_name=_COLLECTION_NAME,
        embedding_function=_EMBEDDING_MODEL,
        client=_chroma_client(),
    )

    results: list[Document] = vectorstore.similarity_search(
        query=query,
        k=1,
        filter={"tenant_id": tenant_id},
    )

    if not results:
        logger.warning(
            "No retrieval results for query='%s', tenant=%s",
            query,
            tenant_id,
        )
        return ""

    document_text: str = results[0].page_content
    logger.info(
        "Retrieved chunk for query='%s', tenant=%s — length=%d",
        query,
        tenant_id,
        len(document_text),
    )
    return document_text