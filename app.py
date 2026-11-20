import re
import requests
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="Study Guide", page_icon="📚")
st.title("📚 Study Guide")

levels = [
    "Class 1", "Class 2", "Class 3", "Class 4", "Class 5",
    "Class 6", "Class 7", "Class 8", "Class 9", "Class 10",
    "Intermediate (HSC)", "BSc level", "Master's level", "Doctorate level",
]

languages = ["Bengali", "English", "Hindi", "Arabic", "Spanish", "French"]

topic = st.text_input("What topic do you want to learn about?")
level = st.selectbox("Which level are you studying at?", levels)
language = st.selectbox("Which language?", languages)
font_size = st.slider("Font size", 14, 28, 18)
font_style = st.selectbox(
    "Font style", ["sans-serif", "serif", "monospace"]
)
show_images = st.checkbox("Show related images", value=True)

st.markdown(
    f"""
    <style>
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {{
        font-size: {font_size}px !important;
        font-family: {font_style} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

SKIP_WORDS = ("icon", "logo", "flag", "portrait", "symbol")

OTHER_LANGS = (
    "es", "de", "fr", "it", "pt", "ru", "zh", "ja", "ko", "ar", "pl",
    "nl", "tr", "sv", "cs", "uk", "vi", "id", "hu", "fa", "he", "ro",
    "ca", "fi", "da", "no", "el", "bg", "sr", "hr", "th", "hi", "bn",
)


def language_tag_score(title):
    """Return 1 if the file name looks English, -1 if another language."""
    name = title.lower().rsplit(".", 1)[0]
    tokens = re.split(r"[\s_\-().,]+", name)
    if "en" in tokens or "english" in tokens:
        return 1
    if any(tok in OTHER_LANGS for tok in tokens):
        return -1
    return 0


def get_commons_images(query, limit=3):
    headers = {"User-Agent": "StudyGuideApp/1.0 (student project)"}
    api = "https://commons.wikimedia.org/w/api.php"
    try:
        data = requests.get(
            api,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f"{query} diagram English",
                "gsrnamespace": 6,
                "gsrlimit": 40,
                "prop": "imageinfo",
                "iiprop": "url|mime|size",
                "iiurlwidth": 600,
                "format": "json",
            },
            headers=headers,
            timeout=15,
        ).json()
        pages = data.get("query", {}).get("pages", {})
        candidates = []
        for page in pages.values():
            title = page.get("title", "")
            lowered = title.lower()
            if any(word in lowered for word in SKIP_WORDS):
                continue
            score = language_tag_score(title)
            if score < 0:
                continue
            info = page.get("imageinfo", [{}])[0]
            if info.get("mime") not in ("image/jpeg", "image/png"):
                continue
            if info.get("width", 0) < 400 or info.get("height", 0) < 300:
                continue
            url = info.get("thumburl") or info.get("url")
            candidates.append((score, url))
        candidates.sort(key=lambda item: item[0], reverse=True)
        return [url for _, url in candidates][:limit]
    except Exception:
        return []


if st.button("Explain it"):
    if not topic.strip():
        st.warning("Please type a topic first.")
    else:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            timeout=60,
            max_retries=1,
        )
        prompt = ChatPromptTemplate.from_template(
            "You are a study helper. Explain {topic} for a student at "
            "{level}. Match the depth, vocabulary and examples to that "
            "level. Answer in {language}."
        )
        chain = prompt | llm
        with st.spinner("Thinking..."):
            try:
                response = chain.invoke(
                    {"topic": topic, "level": level, "language": language}
                )
                st.session_state["answer"] = response.text
                st.session_state["images"] = get_commons_images(topic)
            except Exception as e:
                st.session_state["answer"] = None
                st.error(f"Something went wrong: {e}")

if st.session_state.get("answer"):
    st.markdown(st.session_state["answer"])
    if show_images:
        images = st.session_state.get("images", [])
        if images:
            st.subheader("Related images")
            st.image(images, width=250)
        else:
            st.caption("No related images found.")
