import streamlit as st
import chromadb
import math
from PIL import Image
from cryptography.fernet import Fernet
import numpy as np

st.title("Search Image")

# show all images from chromadb in batch of 50
client = chromadb.PersistentClient(path=f"dbs/{st.user.name}")
db = client.get_collection(name="images")
key_db = client.get_collection(name="keys")
key = key_db.get(ids=["encryption_key"])["documents"][0].encode()
batch_size = 50
cols = 4

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
                image_np = np.frombuffer(decrypted_image, dtype=np.uint8).reshape((metadata["height"], metadata["width"], 3))
                st.image(image_np)