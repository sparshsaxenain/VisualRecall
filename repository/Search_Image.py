import ollama
import streamlit as st
import chromadb
import math
from PIL import Image
from cryptography.fernet import Fernet
import numpy as np
from io import BytesIO
from ollama import chat, embed, pull, ListResponse
import time
import bm25s

if 'embedding_boolean' not in st.session_state:
    st.session_state.embedding_boolean = False

if not st.session_state.embedding_boolean:
    with st.spinner("Downloading embedding model...", show_time=True):
        pull('embeddinggemma:latest', stream=False)
        st.session_state.embedding_boolean = True

st.title("Search Image")
with st.sidebar:
    k = st.slider("Number of results to show", min_value=1, max_value=20, value=5, step=1)

# show all images from chromadb in batch of 50
try:
    client = chromadb.PersistentClient(path=f"dbs/{st.session_state.session_id}")
    db = client.get_collection(name="images")
    key_db = client.get_collection(name="keys")
    key = key_db.get(ids=["encryption_key"])["documents"][0].encode()
except Exception as e:
    st.warning("No images found. Please upload some images first.")
    st.stop()
batch_size = 50
cols = 4

search_query = st.text_input("Search query")
if not search_query:
    total_images = db.count()
    total_pages = max(1, math.ceil(total_images / batch_size))
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    offset = (page - 1) * batch_size
    results = db.get(offset=offset, limit=batch_size, include=["metadatas"])

    for i in range(0, len(results["ids"]), cols):
        columns = st.columns(cols)
        for j in range(cols):
            if i + j < len(results["ids"]):
                with columns[j]:
                    metadata = results["metadatas"][i + j]
                    # Decrypt the image
                    fernet = Fernet(key)
                    with open(metadata["filepath"], "rb") as f:
                        encrypted_image = f.read()
                    decrypted_image = fernet.decrypt(encrypted_image)
                    image = Image.open(BytesIO(decrypted_image)).convert("RGB")
                    st.image(image, width="stretch")
## Only simarity search
# else:
#     start_time = time.time()
#     embedding = embed(
#         model="embeddinggemma:latest",
#         input=search_query
#     )
#     results = db.query(
#         query_embeddings=embedding.embeddings,
#         n_results=k,
#         include=["metadatas", "distances"]
#     )
#     for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
#         # Decrypt the image
#         fernet = Fernet(key)
#         with open(metadata["filepath"], "rb") as f:
#             encrypted_image = f.read()
#         decrypted_image = fernet.decrypt(encrypted_image)
#         image = Image.open(BytesIO(decrypted_image)).convert("RGB")
#         st.image(image, caption=f"{metadata["filename"]} | Similarity: {(1 - distance):.2f}")
#     st.write(f"Search took {time.time() - start_time:.2f} seconds")

## Similarity search + BM25
else:
    start_time = time.time()

    embedding = embed(
        model="embeddinggemma:latest",
        input=search_query
    )

    results = db.query(
        query_embeddings=embedding.embeddings,
        n_results=k,
        include=["metadatas", "distances"]
    )

    best_metadata = {}

    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    corpus = [metadata.get("description", "") for metadata in metadatas]

    corpus_tokens = bm25s.tokenize(corpus)

    retriever = bm25s.BM25(corpus=corpus)
    retriever.index(corpus_tokens)

    query_tokens = bm25s.tokenize(search_query)

    bm25_results, bm25_scores = retriever.retrieve(
        query_tokens,
        k=len(corpus)
    )

    bm25_score_map = {}

    for i in range(bm25_results.shape[1]):
        doc = bm25_results[0, i]
        score = bm25_scores[0, i]
        bm25_score_map[doc] = score

    all_bm25_scores = np.array(list(bm25_score_map.values()))

    bm25_min = np.min(all_bm25_scores)
    bm25_max = np.max(all_bm25_scores)

    for idx, metadata in enumerate(metadatas):
        similarity_score = 1 - distances[idx]

        raw_bm25_score = bm25_score_map.get(metadata.get("description", ""), 0)

        bm25_score = (
            (raw_bm25_score - bm25_min) /
            (bm25_max - bm25_min + 1e-8)
        )

        combined_score = (similarity_score + bm25_score) / 2

        if combined_score > 0.5:
            best_metadata[metadata["filename"]] = {
                "metadata": metadata,
                "similarity_score": similarity_score,
                "bm25_score": bm25_score,
                "combined_score": combined_score
            }

    best_metadata = dict(sorted(best_metadata.items(), key=lambda item: item[1]["combined_score"], reverse=True)[:k])

    for filename, data in best_metadata.items():
        metadata = data["metadata"]

        fernet = Fernet(key)

        with open(metadata["filepath"], "rb") as f:
            encrypted_image = f.read()

        decrypted_image = fernet.decrypt(encrypted_image)
        image = Image.open(BytesIO(decrypted_image)).convert("RGB")

        st.image(
            image,
            caption=(
                f"{metadata['filename']} | "
                f"Similarity: {data['similarity_score']:.2f} | "
                f"BM25: {data['bm25_score']:.2f} | "
                f"Combined: {data['combined_score']:.2f}"
            )
        )

    st.write(f"Search took {time.time() - start_time:.2f} seconds")