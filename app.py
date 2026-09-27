import streamlit as st
from dotenv import load_dotenv
from graph import create_graph

load_dotenv()

from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "chithram.png"

st.set_page_config(
    page_title="CHITHRAM FINDER",
    page_icon="🖼️",
    layout="wide"
)

# Clean minimal CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        max-width: 1100px;
    }
    .hero-wrapper {
        min-height: 30vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .chithram-title {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 700;
        color: inherit;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .chithram-subtitle {
        text-align: center;
        opacity: 0.65;
        font-size: 1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    div[data-testid="stTextInput"] input {
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.95rem;
    }
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        padding: 0.55rem 1rem;
        transition: opacity 0.15s ease;
    }
    .stButton button:hover {
        opacity: 0.85;
    }
    div[data-testid="stExpander"] {
        border-radius: 8px;
    }
    .image-card {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(128,128,128,0.3);
        margin-bottom: 1.2rem;
    }
    .image-caption {
        padding: 0.5rem 0.7rem;
        font-size: 0.8rem;
        opacity: 0.65;
    }
    hr {
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header + search, vertically centered
st.markdown("<div class='hero-wrapper'>", unsafe_allow_html=True)

icon_col1, icon_col2, icon_col3 = st.columns([1, 0.3, 1])
with icon_col2:
    st.image(str(LOGO_PATH), width=180)

st.markdown("<div class='chithram-title'>CHITHRAM FINDER</div>", unsafe_allow_html=True)
st.markdown(
    "<p class='chithram-subtitle'>Describe it. We'll find it.</p>",
    unsafe_allow_html=True
)

left_space, center, right_space = st.columns([1, 2, 1])
with center:
    context = st.text_input(
        "",
        placeholder="e.g. a laptop showing a dashboard on a wooden desk near a window",
        label_visibility="collapsed"
    )
    search_clicked = st.button("Search", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Results
if search_clicked and context:
    with st.spinner("Searching Pexels, Unsplash and Pixabay..."):
        graph = create_graph()
        result = graph.invoke({
            "context": context,
            "queries": [],
            "structured_info": None,
            "pexels_images": [],
            "unsplash_images": [],
            "pixabay_images": [],
            "images": []
        })

    st.markdown("<hr>", unsafe_allow_html=True)

    if result["structured_info"]:
        info = result["structured_info"]
        with st.expander("Understood description as"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Main subject**  \n{info.get('main_subject', '—')}")
                st.markdown(f"**Environment**  \n{info.get('environment', '—')}")
                st.markdown(f"**Device**  \n{info.get('device', '—')}")
            with c2:
                st.markdown(f"**Screen content**  \n{info.get('screen_content', '—')}")
                st.markdown(f"**Style**  \n{info.get('style', '—')}")

    with st.expander("Search queries used"):
        for query in result["queries"]:
            st.write("•", query)

    st.markdown(f"**{len(result['images'])} images found**")
    st.write("")

    if result["images"]:
        columns = st.columns(3)
        for i, image in enumerate(result["images"]):
            column = columns[i % 3]
            with column:
                st.markdown("<div class='image-card'>", unsafe_allow_html=True)
                st.image(image.image_url, use_container_width=True)
                st.markdown(
                    f"<div class='image-caption'>{image.source} — {image.photographer}</div>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No images found — try rephrasing your description.")

elif search_clicked and not context:
    st.warning("Type a description first.")