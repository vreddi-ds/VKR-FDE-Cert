"""
MARA Hybrid Retrieval.

Load synthetic mainframe incident records and retrieve
relevant evidence using BM25, dense embeddings, and RRF.

This module supports the TC3 evidence-grounded API endpoint.
"""

import json
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from rank_bm25 import BM25Okapi


# Locate the repository root relative to this Python file.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Path to the 15 synthetic mainframe incident records.
CORPUS_PATH = REPO_ROOT / "use_case" / "data" / "synthetic_v1.jsonl"
# MARA retrieval configuration
DEFAULT_RETRIEVAL_K = 5
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

def load_incidents() -> list[dict]:
    """Load synthetic mainframe incidents from the JSONL corpus."""

    incidents = []

    with CORPUS_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                incident = json.loads(line)
                incidents.append(incident)

    return incidents

def build_chunks(incidents: list[dict]) -> list[dict]:
    """Convert incident records into searchable text chunks."""

    chunks = []

    for incident in incidents:
        job_name = incident["input"]["job_name"]
        content = json.dumps(incident, indent=2)

        chunk = {
            "id": job_name,
            "modality": "text",
            "content": content,
        }

        chunks.append(chunk)

    return chunks

def tokenize(text: str) -> list[str]:
    """Convert text into lowercase searchable tokens."""

    return text.lower().split()


def build_bm25(chunks: list[dict]) -> BM25Okapi:
    """Build a BM25 search index from incident chunks."""

    tokenized_chunks = []

    for chunk in chunks:
        tokens = tokenize(chunk["content"])
        tokenized_chunks.append(tokens)

    return BM25Okapi(tokenized_chunks)


def retrieve_bm25(
    query: str,
    chunks: list[dict],
    bm25: BM25Okapi,
    k: int = DEFAULT_RETRIEVAL_K,
) -> list[dict]:
    """Return the top-k incident records ranked by BM25 relevance."""

    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)

    order = sorted(
        range(len(chunks)),
        key=lambda index: scores[index],
        reverse=True,
    )[:k]

    results = []

    for index in order:
        hit = {
            "id": chunks[index]["id"],
            "modality": chunks[index]["modality"],
            "content": chunks[index]["content"],
            "score": float(scores[index]),
        }
        results.append(hit)

    return results

def build_embedder(
        model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> TextEmbedding:
    """Initialize the selected local embedding model for MARA retrieval."""

    model = TextEmbedding(
        model_name=model_name
    )

    return model

def build_qdrant(
    chunks: list[dict],
    embedder: TextEmbedding,
) -> QdrantClient:
    """Create an in-memory Qdrant index for MARA incidents."""

    # Convert the incident texts into embedding vectors.
    texts = [chunk["content"] for chunk in chunks]
    vectors = list(embedder.embed(texts))

    # Create an in-memory Qdrant client.
    client = QdrantClient(":memory:")

    # Determine the vector dimensions from the selected model.
    vector_size = len(vectors[0])

    client.create_collection(
        collection_name="mara_incidents",
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    # Store each incident's vector and supporting evidence.
    points = []

    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        point = PointStruct(
            id=index,
            vector=vector.tolist(),
            payload={
                "id": chunk["id"],
                "modality": chunk["modality"],
                "content": chunk["content"],
            },
        )

        points.append(point)

    client.upsert(
        collection_name="mara_incidents",
        points=points,
    )

    return client

def retrieve_dense(
    query: str,
    client: QdrantClient,
    embedder: TextEmbedding,
    k: int = DEFAULT_RETRIEVAL_K,
) -> list[dict]:
    """Retrieve the top-k incidents using embedding similarity."""

    # Convert the question into a numeric vector.
    query_vectors = list(embedder.embed([query]))
    query_vector = query_vectors[0].tolist()

    # Search our Qdrant collection & find the most similar stored vectors
    response = client.query_points(
        collection_name="mara_incidents",
        query=query_vector,
        limit=k,
        with_payload=True,
    )

    # Convert Qdrant results into the same format as BM25 results.
    results = []

    for point in response.points:
        hit = {
            "id": point.payload["id"],
            "modality": point.payload["modality"],
            "content": point.payload["content"],
            "score": float(point.score), # Qdrants similarity score
        }

        results.append(hit)

    return results

def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    k: int = 60,
) -> list[dict]:
    """Combine ranked retrieval results using their positions, not raw scores."""

    fused = {}
    keep = {}

    for results in result_lists:
        for rank, hit in enumerate(results):
            key = (hit["modality"], hit["id"])

            fused[key] = fused.get(key, 0.0) + 1.0 / (k + rank + 1)

            keep[key] = {
                **hit,
                "score": round(fused[key], 4),
            }

    order = sorted(fused, key=fused.get, reverse=True)

    return [keep[key] for key in order]

def retrieve_hybrid(
    query: str,
    chunks: list[dict],
    bm25: BM25Okapi,
    client: QdrantClient,
    embedder: TextEmbedding,
    k: int = DEFAULT_RETRIEVAL_K,
) -> list[dict]:
    """Retrieve incident evidence using BM25, dense search, and RRF."""

    text_hits = retrieve_bm25(query, chunks, bm25, k)
    dense_hits = retrieve_dense(query, client, embedder, k)

    fused_hits = reciprocal_rank_fusion([text_hits, dense_hits])

    return fused_hits[:k]

def initialize_retrieval() -> tuple[list[dict], BM25Okapi, QdrantClient, TextEmbedding]:
    """Load MARA's incident corpus and initialize both retrieval indexes."""

    incidents = load_incidents()
    chunks = build_chunks(incidents)

    bm25 = build_bm25(chunks)
    embedder = build_embedder()
    client = build_qdrant(chunks, embedder)

    return chunks, bm25, client, embedder