import streamlit as st
import requests
import json
import os
from pypdf import PdfReader

# -------- SETTINGS --------
LOCAL_MODEL = "qwen2.5-coder:1.5b"
OPENROUTER_API_KEY = "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"

CHAT_FILE = "chats.json"

# -------- PAGE CONFIG --------
st.set_page_config(page_title="Nexus Pi X", layout="wide")

# -------- LOAD MEMORY --------
if os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "r") as f:
        all_chats = json.load(f)
else:
    all_chats = {"Chat 1": []}

if "all_chats" not in st.session_state:
    st.session_state.all_chats = all_chats

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

# -------- SIDEBAR --------
st.sidebar.title("🧠 Nexus Pi X")

use_cloud = st.sidebar.toggle("☁️ Cloud AI (Smart)", value=True)

if st.sidebar.button("➕ New Chat"):
    new_chat = f"Chat {len(st.session_state.all_chats) + 1}"
    st.session_state.all_chats[new_chat] = []
    st.session_state.current_chat = new_chat

st.sidebar.markdown("### Chats")

for chat in st.session_state.all_chats:
    if st.sidebar.button(chat, use_container_width=True):
        st.session_state.current_chat = chat

# -------- FILE UPLOAD --------
uploaded_file = st.sidebar.file_uploader(
    "Upload file", type=["pdf", "txt", "html", "py"]
)

file_content = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            file_content += page.extract_text() or ""
    else:
        file_content = uploaded_file.read().decode("utf-8", errors="ignore")

    st.sidebar.success("File loaded")

# -------- AI FUNCTION --------
def ask_ai(prompt):

    if use_cloud:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}"
            }

            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }

            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            return res.json()["choices"][0]["message"]["content"]

        except Exception as e:
            return f"Cloud error: {e}"

    # -------- LOCAL --------
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": LOCAL_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        return response.json()["response"]

    except:
        return "Local model not running"

# -------- MAIN UI --------
st.title("💬 Nexus Pi X")

chat_history = st.session_state.all_chats[st.session_state.current_chat]

# -------- DISPLAY CHAT --------
for msg in chat_history:
    role = "user" if msg["role"] == "User" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])

# -------- INPUT --------
user_input = st.chat_input("Type your message...")

# -------- PROCESS --------
if user_input:

    history_text = ""
    for msg in chat_history:
        history_text += f"{msg['role']}: {msg['content']}\n"

    full_prompt = f"""
You are Nexus Pi X, an advanced AI assistant.

Rules:
- Be clear, direct, and useful
- Think step-by-step
- Give best optimized answers
- Avoid unnecessary long text

If coding:
- Give clean working code
- Explain briefly

FILE:
{file_content}

CHAT HISTORY:
{history_text}

User: {user_input}
"""

    reply = ask_ai(full_prompt)

    chat_history.append({"role": "User", "content": user_input})
    chat_history.append({"role": "AI", "content": reply})

    with open(CHAT_FILE, "w") as f:
        json.dump(st.session_state.all_chats, f)

    st.rerun()

# -------- SAVE HTML --------
col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Save last response as HTML"):
        if chat_history:
            with open("output.html", "w", encoding="utf-8") as f:
                f.write(chat_history[-1]["content"])
            st.success("Saved as output.html")

with col2:
    if st.button("🧹 Clear Chat"):
        st.session_state.all_chats[st.session_state.current_chat] = []
        with open(CHAT_FILE, "w") as f:
            json.dump(st.session_state.all_chats, f)
        st.rerun()