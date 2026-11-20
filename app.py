import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="Study Helper", page_icon="📚")
st.title("📚 Study Helper")

levels = [
    "Class 1", "Class 2", "Class 3", "Class 4", "Class 5",
    "Class 6", "Class 7", "Class 8", "Class 9", "Class 10",
    "Intermediate (HSC)", "BSc level", "Master's level", "Doctorate level",
]

languages = ["Bengali", "English", "Hindi", "Arabic", "Spanish", "French"]

topic = st.text_input("What topic do you want to learn about?")
level = st.selectbox("Which level are you studying at?", levels)
language = st.selectbox("Which language?", languages)

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
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Something went wrong: {e}")