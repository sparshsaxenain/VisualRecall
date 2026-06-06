import streamlit as st
import chromadb
import uuid
from PIL import Image
import os
import json
import hashlib
import numpy as np
from cryptography.fernet import Fernet

st.title("Upload Image")

uploaded_files = st.file_uploader("Upload your images", accept_multiple_files=True, type=["jpg", "jpeg", "png"], label_visibility="hidden")
client = chromadb.PersistentClient(path=f"dbs/{st.user.name}")
db = client.get_or_create_collection(name="images")
key_db = client.get_or_create_collection(name="keys")
if key_db.count() == 0:
    key = Fernet.generate_key()
    key_db.add(ids=["encryption_key"], documents=[key.decode()])

with st.sidebar:
    LLM_CONFIG = json.load(open(".streamlit/model_list.json"))
    LLM_provider = st.selectbox("Select LLM Provider", options=list(LLM_CONFIG.keys()))
    LLM_model = st.selectbox("Select LLM Model", options=LLM_CONFIG[LLM_provider])

i = 0
for uploaded_file in uploaded_files:
    image = Image.open(uploaded_file).convert("RGB")
    id = hashlib.sha256(image.tobytes()).hexdigest()
    image_np = np.array(image)

    # Encrypt and save the image to disk
    key = key_db.get(ids=["encryption_key"])["documents"][0].encode()
    fernet = Fernet(key)
    encrypted_image = fernet.encrypt(image.tobytes())
    os.makedirs("encrypted_images", exist_ok=True)
    with open(f"encrypted_images/{id}.enc", "wb") as f:
        f.write(encrypted_image)

    # metadata
    metadata = {
        "filename": uploaded_file.name,
        "filetype": uploaded_file.type,
        "filesize": uploaded_file.size,
        "width": None,
        "height": None,
        "description": None,
        "filepath": f"encrypted_images/{id}.enc"
    }
    metadata["width"], metadata["height"] = image.size
    description = ""
    # Get description from LLM
    if LLM_provider == "OpenAI":
        # Call OpenAI API to get description
        pass
    elif LLM_provider == "Ollama":
        # Call Ollama API to get description
        pass
    metadata["description"] = description

    # add to chromadb
    db.add(
        ids=[id],
        embeddings=[[i * 0.1]],  # Placeholder for image embeddings
        documents=[f"uploaded_images/{uploaded_file.name}"],
        metadatas=[metadata],
        images=[image_np]
    )
    st.image(Image.fromarray(image_np), caption=uploaded_file.name)
    i += 1