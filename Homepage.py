from pathlib import Path

import streamlit as st


PLAN_DIAGRAM = Path("assets/plan.png")


def render_homepage() -> None:
    if not st.user.is_logged_in:
        st.warning(
            "Login is required to upload and search your own image library. "
            "To get test access, raise an issue with your email address and "
            "access will be enabled within 24 hours."
        )
        st.button("Log in with Google", on_click=st.login)
    else:
        st.success("You are logged in and can use Upload Image and Search Image.")

    st.title("Visual Recall")
    st.caption("Private, AI-powered image memory for search, browsing, and retrieval.")

    st.markdown(
        """
Visual Recall turns screenshots, photos, reference images, UI captures, diagrams,
documents, and visual notes into a searchable personal image library. It builds a
retrieval index that lets you find images later with natural-language queries.

Instead of relying only on image names, Visual Recall generates detailed visual
descriptions, embeds those descriptions into a vector database, encrypts the
original image content, and combines semantic search with keyword matching when
you search.
"""
    )

    st.divider()

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("1. Upload")
        st.write(
            "Add one or many JPG, JPEG, or PNG images. Duplicate uploads are "
            "skipped using a content-based hash tied to your user account."
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
            "Browse your image gallery or search by concepts, objects, colors, "
            "text, layout, scene details, and other visible attributes."
        )

    st.divider()

    st.header("Current Flow")

    if PLAN_DIAGRAM.exists():
        st.image(
            str(PLAN_DIAGRAM),
            caption="Current Visual Recall upload, indexing, and search flow.",
            width="stretch",
        )
    else:
        st.info("The current flow diagram will appear here when available.")

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
- Fernet encryption protects the saved image content.
- Gallery mode lets you browse uploaded images in paginated batches.
- Search mode ranks results with vector similarity plus BM25 keyword matching.
"""
        )

    with feature_col_2:
        st.markdown(
            """
### What gets stored

- Image metadata such as name, type, size, width, and height.
- A detailed generated description of visible content.
- An embedding created from the description with `embeddinggemma:latest`.
- A per-user ChromaDB collection for search and retrieval.
"""
        )

    st.info(
        "Your original image content is encrypted, while searchable metadata and "
        "vectors are stored in ChromaDB."
    )

    st.header("Technical Architecture")

    tech_tab_1, tech_tab_2, tech_tab_3 = st.tabs(
        ["Upload pipeline", "Search pipeline", "Storage and security"]
    )

    with tech_tab_1:
        st.markdown(
            """
### Upload pipeline

1. The Streamlit uploader accepts common image formats.
2. Each image is normalized to RGB with Pillow and serialized as PNG bytes.
3. A SHA-256 hash of the image bytes plus the logged-in user name becomes the
   stable image id.
4. The app checks ChromaDB before indexing, so duplicate images are skipped.
5. The selected vision model, through OpenAI or Ollama, generates a detailed
   objective description of visible image content.
6. Ollama `embeddinggemma:latest` converts that description into an embedding.
7. ChromaDB stores the id, embedding, metadata, generated description, and image
   array reference.
"""
        )

    with tech_tab_2:
        st.markdown(
            """
### Search pipeline

1. The user's query is embedded with the same `embeddinggemma:latest` model.
2. ChromaDB performs cosine-similarity search over the stored description vectors.
3. The candidate descriptions are tokenized and indexed with BM25.
4. BM25 scores are normalized across the candidate set.
5. The final result score averages semantic similarity and normalized BM25.
6. Results with a combined score above the current threshold are shown with their
   component scores.

This hybrid design helps with both fuzzy concept search and exact keyword search.
For example, semantic similarity can find "finance dashboard" even when the exact
words differ, while BM25 can reward exact visible words such as labels, signs, or
UI text.
"""
        )

    with tech_tab_3:
        st.markdown(
            """
### Storage and security model

- ChromaDB persists per-user retrieval data locally.
- A `keys` collection stores the Fernet encryption key used for image content.
- Original image bytes are encrypted with Fernet before persistence.
- Search and gallery views decrypt images only when they need to be displayed.
- Streamlit user authentication keeps each user's retrieval space separate.

The current design is local-first and practical for a personal or prototype image
retrieval system. For a production deployment, key management, user-id handling,
access controls, backups, and retention policies should be hardened.
"""
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
2. Select one or more JPG, JPEG, or PNG images.
3. Choose the vision model provider and model in the sidebar.
4. Wait while each image is described, embedded, encrypted, and indexed.
5. Review the preview and processing time shown after each successful upload.

During upload, Visual Recall creates a neutral description of the image. The best
descriptions mention objects, people, text, colors, scene layout, foreground and
background details, and anything else that could help you find the image later.
"""
        )

        if st.user.is_logged_in:
            st.page_link(
                "repository/Upload_Image.py",
                label="Go to Upload Image",
                icon=":material/upload:",
            )
        else:
            st.info("Log in to open Upload Image.")

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

        if st.user.is_logged_in:
            st.page_link(
                "repository/Search_Image.py",
                label="Go to Search Image",
                icon=":material/search:",
            )
        else:
            st.info("Log in to open Search Image.")

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

    st.header("Future Implementation")

    future_col_1, future_col_2 = st.columns(2)

    with future_col_1:
        st.markdown(
            """
### Video support with audio

- Upload videos in addition to images.
- Extract representative frames for visual indexing.
- Transcribe audio into searchable text.
- Combine frame descriptions, audio transcript, timestamps, and metadata.
- Return results that can jump to the most relevant moment in the video.
"""
        )

    with future_col_2:
        st.markdown(
            """
### Current search flow plus attention score

- Keep the existing semantic similarity and BM25 hybrid ranking.
- Add an attention score that estimates how strongly an image or frame matches
  the most important parts of the query.
- Weight exact visual entities, detected text, object prominence, and spatial
  relevance more explicitly.
- Show the attention score beside similarity, BM25, and combined score for more
  transparent ranking.
"""
        )

    st.success(
        "Visual Recall is ready when uploaded images appear in the gallery and "
        "natural-language searches return the images you expected."
    )


st.set_page_config(page_title="Visual Recall", page_icon=":mag:", layout="wide")

menu_pages = [st.Page(render_homepage, title="Home", icon=":material/home:")]

if st.user.is_logged_in:
    menu_pages.extend(
        [
            st.Page("repository/Upload_Image.py", title="Upload Image", icon=":material/upload:"),
            st.Page("repository/Search_Image.py", title="Search Image", icon=":material/search:"),
        ]
    )

pages = {"Menu": menu_pages}

pg = st.navigation(pages)
pg.run()

# if st.user.is_logged_in:
#     with st.sidebar:
#         st.button("Log out", on_click=st.logout)
#         display_name = " ".join(st.user.name.split()[:2])
#         st.write(f"Logged in as: {display_name}\n({st.user.email})")
