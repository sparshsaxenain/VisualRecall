import streamlit as st
from ollama import pull

st.title("Visual Recall")
st.caption("Private, AI-powered image memory for search, browsing, and retrieval.")

st.markdown(
    """
Visual Recall turns a folder of images into a searchable personal image library.
Upload screenshots, photos, reference images, UI captures, diagrams, documents, or
visual notes, and the app builds a retrieval index that lets you find them later
with natural-language queries.

Instead of relying only on filenames, Visual Recall generates detailed visual
descriptions, embeds those descriptions into a vector database, stores encrypted
image files on disk, and combines semantic search with keyword matching when you
search.
"""
)

st.divider()

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("1. Upload")
    st.write(
        "Add one or many JPG, JPEG, or PNG images. Duplicate uploads are skipped "
        "using a content-based hash tied to your user account."
    )

with col_b:
    st.subheader("2. Understand")
    st.write(
        "Choose an OpenAI or Ollama vision model. The app creates a factual, "
        "retrieval-focused description of every image."
    )

with col_c:
    st.subheader("3. Search")
    st.write(
        "Browse your image gallery or search by concepts, objects, colors, text, "
        "layout, scene details, and other visible attributes."
    )

st.divider()

st.header("What This App Does")

feature_col_1, feature_col_2 = st.columns(2)

with feature_col_1:
    st.markdown(
        """
### Current functionality

- Google login keeps each user's image index separate.
- Multi-image upload supports common web image formats.
- AI image captioning produces detailed visual descriptions for retrieval.
- ChromaDB stores image metadata, descriptions, and embeddings locally.
- Fernet encryption protects the saved image files.
- Gallery mode lets you browse uploaded images in paginated batches.
- Search mode ranks results with vector similarity plus BM25 keyword matching.
"""
    )

with feature_col_2:
    st.markdown(
        """
### What gets stored

- The encrypted image file in `encrypted_images/`.
- Image metadata such as filename, type, size, width, and height.
- A detailed generated description of visible content.
- An embedding created from the description with `embeddinggemma:latest`.
- A per-user ChromaDB collection under `dbs/<user name>/`.
"""
    )

st.info(
    "Your original images are not saved as plain image files by this app. They are "
    "encrypted before being written to disk, while searchable metadata and vectors "
    "are stored in ChromaDB."
)

st.header("How To Use It")

tab_upload, tab_search, tab_tips = st.tabs(
    ["Upload images", "Search images", "Better results"]
)

with tab_upload:
    st.markdown(
        """
### Upload workflow

1. Open **Upload Image** from the sidebar.
2. Select one or more `.jpg`, `.jpeg`, or `.png` files.
3. Choose the vision model provider and model in the sidebar.
4. Wait while each image is described, embedded, encrypted, and indexed.
5. Review the preview and processing time shown after each successful upload.

During upload, Visual Recall creates a neutral description of the image. The best
descriptions mention objects, people, text, colors, scene layout, foreground and
background details, and anything else that could help you find the image later.
"""
    )

    st.page_link(
        "repository/Upload_Image.py",
        label="Go to Upload Image",
        icon=":material/upload:",
    )

with tab_search:
    st.markdown(
        """
### Search workflow

1. Open **Search Image** from the sidebar.
2. Leave the search box empty to browse your gallery.
3. Use the page selector to move through large collections.
4. Enter a natural-language query to search your indexed images.
5. Adjust the result count slider in the sidebar when you need more or fewer matches.

Search uses two signals together:

- **Semantic similarity** finds images whose generated descriptions mean something
  similar to your query.
- **BM25 keyword matching** rewards direct word overlap, which helps with exact
  objects, colors, labels, signs, or visible text.
"""
    )

    st.page_link(
        "repository/Search_Image.py",
        label="Go to Search Image",
        icon=":material/search:",
    )

with tab_tips:
    st.markdown(
        """
### Query examples

- `red car parked in front of a glass building`
- `whiteboard diagram with arrows and product architecture`
- `invoice screenshot with table and totals`
- `person wearing blue shirt near a laptop`
- `dark UI dashboard with revenue chart`
- `image containing handwritten notes`

### Practical tips

- Search for visible facts, not hidden meaning.
- Include colors, layout, object names, and any visible text when you know them.
- If a result is missing, try a broader query first, then add specific details.
- For screenshots, search by UI labels, page type, chart type, or layout.
- Upload high-resolution images when possible so the description model can see
  small details and text.
"""
    )

st.header("Setup Checklist")

st.markdown(
    """
Before using the app heavily, make sure these pieces are available:

- Streamlit authentication is configured for Google login.
- `.streamlit/secrets.toml` contains `OpenAI_key` if you use OpenAI models.
- `.streamlit/model_list.json` lists the providers and models you want in the UI.
- Ollama is running locally if you choose the Ollama provider.
- The `embeddinggemma:latest` embedding model is available to Ollama.
- The app has write access to `dbs/` and `encrypted_images/`.
"""
)

st.warning(
    "Do not delete `dbs/` or `encrypted_images/` unless you intentionally want to "
    "remove the indexed metadata or encrypted image files."
)

st.header("Recommended First Run")

st.markdown(
    """
1. Upload 5 to 10 varied test images.
2. Search for broad concepts such as `dashboard`, `receipt`, or `street scene`.
3. Search for narrow details such as a color, visible word, or object.
4. Compare the returned similarity, BM25, and combined scores.
5. If results look good, upload the rest of your library in batches.
"""
)

st.success(
    "Visual Recall is ready when uploaded images appear in the gallery and natural "
    "language searches return the images you expected."
)
