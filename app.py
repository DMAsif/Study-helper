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

LANG_CODES = {
    "Bengali": "bn",
    "English": "en",
    "Hindi": "hi",
    "Arabic": "ar",
    "Spanish": "es",
    "French": "fr",
}

topic = st.text_input("What topic do you want to learn about?")
level = st.selectbox("Which level are you studying at?", levels)
language = st.selectbox("Which language?", list(LANG_CODES))
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

HEADERS = {"User-Agent": "StudyGuideApp/1.0 (student project)"}
SKIP_WORDS = (
    "icon", "logo", "flag", "portrait", "symbol", "commons-logo",
    "wiki", "edit", "question", "ambox", "stub",
)


def make_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=1,
    )


def translate_topic(text, target_language):
    if target_language == "English":
        return text
    try:
        reply = make_llm().invoke(
            f"Translate this study topic into {target_language}. "
            f"Reply with only the translated words, nothing else: {text}"
        )
        return reply.text.strip() or text
    except Exception:
        return text


def images_from_wikipedia(query, code, limit=3):
    api = f"https://{code}.wikipedia.org/w/api.php"
    try:
        search = requests.get(
            api,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "format": "json",
            },
            headers=HEADERS,
            timeout=15,
        ).json()
        hits = search.get("query", {}).get("search", [])
        if not hits:
            return []
        title = hits[0]["title"]

        data = requests.get(
            api,
            params={
                "action": "query",
                "titles": title,
                "generator": "images",
                "gimlimit": 40,
                "prop": "imageinfo",
                "iiprop": "url|mime|size",
                "iiurlwidth": 600,
                "format": "json",
            },
            headers=HEADERS,
            timeout=15,
        ).json()
        pages = data.get("query", {}).get("pages", {})
        urls = []
        for page in pages.values():
            name = page.get("title", "").lower()
            if any(word in name for word in SKIP_WORDS):
                continue
            info = page.get("imageinfo", [{}])[0]
            if info.get("mime") not in ("image/jpeg", "image/png"):
                continue
            if info.get("width", 0) < 400 or info.get("height", 0) < 300:
                continue
            urls.append(info.get("thumburl") or info.get("url"))
        return urls[:limit]
    except Exception:
        return []


def get_images(topic_text, language_name):
    code = LANG_CODES[language_name]
    translated = translate_topic(topic_text, language_name)
    images = images_from_wikipedia(translated, code)
    if not images and code != "en":
        images = images_from_wikipedia(topic_text, "en")
    return images


if st.button("Explain it"):
    if not topic.strip():
        st.warning("Please type a topic first.")
    else:
        prompt = ChatPromptTemplate.from_template(
            "You are a study helper. Explain {topic} for a student at "
            "{level}. Match the depth, vocabulary and examples to that "
            "level. Answer in {language}."
        )
        chain = prompt | make_llm()
        with st.spinner("Thinking..."):
            try:
                response = chain.invoke(
                    {"topic": topic, "level": level, "language": language}
                )
                st.session_state["answer"] = response.text
                st.session_state["images"] = (
                    get_images(topic, language) if show_images else []
                )
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
