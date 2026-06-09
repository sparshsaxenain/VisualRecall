import streamlit as st
import chromadb
import uuid
from PIL import Image
import os
import json
import hashlib
import numpy as np
from cryptography.fernet import Fernet
from ollama import chat, embed, Client, pull
import base64
from pathlib import Path
import time
from io import BytesIO
import bm25s
from openai import OpenAI

st.title("Upload Image")
openai_client = OpenAI(
    api_key = st.secrets["OpenAI_key"]
)
ollama_client = Client(
    host='https://ollama.com',
    headers={'Authorization': 'Bearer ' + st.secrets['OLLAMA_API_KEY']}
)

if 'embedding_boolean' not in st.session_state:
    st.session_state.embedding_boolean = False

if not st.session_state.embedding_boolean:
    with st.spinner("Downloading embedding model...", show_time=True):
        pull('embeddinggemma:latest', stream=False)
        st.session_state.embedding_boolean = True

uploaded_files = st.file_uploader("Upload your images", accept_multiple_files=True, type=["jpg", "jpeg", "png"], label_visibility="hidden")
client = chromadb.PersistentClient(path=f"dbs/{st.user.name}")
db = client.get_or_create_collection(
    name="images",
    configuration = {
        "hnsw":{
            "space": "cosine"
        }
    }
)
key_db = client.get_or_create_collection(name="keys")
if key_db.count() == 0:
    key = Fernet.generate_key()
    key_db.add(ids=["encryption_key"], documents=[key.decode()])

with st.sidebar:
    if 'LLM_CONFIG' not in st.session_state or 'LLM_CONFIG' in st.session_state:
        st.session_state.LLM_CONFIG = json.load(open(".streamlit/model_list.json"))
    if 'LLM_provider' not in st.session_state or 'LLM_provider' in st.session_state:
        st.session_state.LLM_provider = st.selectbox("Select LLM Provider", options=list(st.session_state.LLM_CONFIG.keys()))
    if 'LLM_model' not in st.session_state or 'LLM_model' in st.session_state:
        st.session_state.LLM_model = st.selectbox("Select LLM Model", options=st.session_state.LLM_CONFIG[st.session_state.LLM_provider])

progress_text = "Operation in progress. Please wait."
progress_bar = st.progress(0, text=progress_text)
for percent_complete, uploaded_file in enumerate(uploaded_files, start=1):
    image = Image.open(uploaded_file).convert("RGB")
    start_time = time.time()
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    id = hashlib.sha256(image_bytes + st.user.name.encode()).hexdigest()
    if db.get(ids=[id])["ids"]:
        st.warning(f"{uploaded_file.name} already exists in the database. Skipping upload.")
        continue
    image_np = np.array(image)

    key = key_db.get(ids=["encryption_key"])["documents"][0].encode()
    fernet = Fernet(key)

    encrypted_image = fernet.encrypt(image_bytes)

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
    system_prompt = """Generate a highly detailed, objective description of an input image, with the explicit goal of maximizing its usefulness for Retrieval-Augmented Generation (RAG) systems and downstream search or retrieval tasks. \n\nThe description should:\n- Enumerate all visible objects, people, actions, scene settings, colors, and other relevant attributes.\n- Avoid subjective impressions, emotion, or poetic/philosophical interpretations.\n- Include details about spatial arrangements (positions, relative sizes, foreground/background relationships).\n- Capture information relevant to categorization (e.g., “a red sedan car parked beside a yellow school bus in front of a modern glass building”).\n- Mention textual content if present (e.g., signage, book titles, device screens).\n- If elements are ambiguous or unclear, note them as [uncertain object], [unclear text], etc.\n- Remain entirely neutral and fact-based.\n\nBefore writing the description, analyze the image to identify all pertinent details and structure your thoughts step-by-step. Only after completing this internal reasoning, produce the full description.\n\nOutput Format:\n- Respond with one comprehensive, logically structured paragraph.\n- Use clear, specific language, listing details in order from most prominent to least prominent.\n- Do not use line breaks, code blocks, or markdown formatting.\n\nExample Input/Output:\n---\n**Input:** [Image depicting a city street with various vehicles, storefronts, and pedestrians.]\n**Internal reasoning (not output):**\n- Identify scene type: city street, daylight\n- List notable objects: cars (red sedan, yellow taxi), bus (yellow), multiple storefronts with visible signs (“Bakery”, “Salon”), pedestrians (3, male and female; clothing colors and positions)\n- Note spatial arrangement: vehicles on the street, bus in background, pedestrians on sidewalk in front of stores\n- Extract text from signs\n- Note any prominent colors, actions (walking, standing, car driving)\n\n**Output:**\nA busy urban street scene in daylight shows a red sedan and a yellow taxi driving along a gray asphalt road, with a large yellow school bus parked in the background. Multiple pedestrians are present: two women and one man walk on the sidewalk, passing by storefronts with visible signage reading “Bakery” and “Salon.” The buildings have glass facades with reflections, and trees line the street on the right side. The sky is partly cloudy, and traffic signals are visible at the intersection.\n\n---\n(For real examples, extend to all relevant details visible in the image; the above is a representative sample.)\n\nEdge Cases / Important Considerations:\n- If the image contains low resolution or unclear sections, use [uncertain object] or [unclear text] placeholders.\n- List all textual information, even partial or garbled text, as accurately as possible.\n- Focus on explicit, observable details; do not infer context beyond what is clearly visible.\n\nReminder: Your main objective is to generate detailed, neutral image descriptions optimized for retrieval and search applications. Always analyze the image step-by-step before forming your response, and provide the final description as a single paragraph."""
    if st.session_state.LLM_provider == "OpenAI":
        # Call OpenAI API to get description
        response = openai_client.responses.create(
            model=st.session_state.LLM_model,
            input = [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Generate a detailed, objective description of the provided image to maximize the effectiveness of Retrieval-Augmented Generation (RAG) and information retrieval systems.\n\n- Focus on factual, concrete elements visible in the image. Describe key objects, people, activities, settings, spatial relationships, colors, and any notable details.\n- Avoid subjective judgments, opinions, or speculative interpretations.\n- Do not include any references to non-visible historical, cultural, or semantic knowledge—only describe what is actually present in the image.\n- Be thorough enough to differentiate this image from other, similar images for retrieval purposes.\n- Write in clear, concise complete sentences.\n\n**Output format:**  \nA single, detailed paragraph (5–8 sentences) summarizing all important visual elements and relationships in the image.\n\n**Example:**  \n*Input*: [photo shows a busy farmers market]  \n*Output*:  \nA crowded outdoor farmers market is depicted in daylight. Numerous people are walking between rows of stalls covered with colorful canopies. Vendors display fresh produce such as tomatoes, lettuce, and apples in crates along wooden tables. Several shoppers carry reusable grocery bags. In the background, a brick building with arched windows is visible. The sky is clear blue, and sunlight casts defined shadows. Signs with handwritten prices are attached to some of the tables, and a bicycle is parked near one of the stalls. The scene conveys a sense of community activity and abundance.\n\n_Reminder: Your goal is to generate a factual, thorough visual description to enable precise retrieval or RAG-based search._"
                        },
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Describe the following image in detail: "
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{uploaded_file.type};base64,{base64.b64encode(image_bytes).decode('utf-8')}",
                            "detail": "original"
                        }
                    ]
                }
            ],
            text={
                "format": {
                "type": "text"
                },
                "verbosity": "medium"
            },
            reasoning={
                "effort": "medium",
                "summary": "auto"
            },
            tools=[],
            store=True,
            include=[
                "reasoning.encrypted_content",
                "web_search_call.action.sources"
            ]
        )
        description = response.output[1].content[0].text
    elif st.session_state.LLM_provider == "Ollama":
        img = base64.b64encode(image_bytes).decode("utf-8")

        response = ollama_client.chat(
            model=st.session_state.LLM_model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": "Describe the following image in detail: ",
                    "images": [img],
                }
            ],
            think = False,
        )

        description = response.message.content
    metadata["description"] = description

    # create embedding for the image description using LLM
    embedding = embed(
        model = "embeddinggemma:latest",
        input = description
    )

    # add to chromadb
    db.add(
        ids=[id],
        embeddings= embedding.embeddings,
        documents=[f"uploaded_images/{uploaded_file.name}"],
        metadatas=[metadata],
        images=[image_np]
    )
    st.image(Image.fromarray(image_np), caption=uploaded_file.name)
    end_time = time.time()
    progress_bar.progress(percent_complete / len(uploaded_files), text=f"Time taken to process {uploaded_file.name}: {end_time - start_time:.2f} seconds")
progress_bar.empty()
uploaded_files.clear()