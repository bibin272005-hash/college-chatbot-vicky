import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ No Gemini API key found! Add GEMINI_API_KEY to your .env file.")
    st.stop()

# -----------------------------
# Create Gemini client
# -----------------------------
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-flash"

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="VICKY - VKIT College Chatbot", layout="centered")
st.title("🤖 VICKY - 🎓VKIT College Assistant")
st.markdown("Hi! I'm **Vicky**, your VKIT College assistant. How may I help you today? 😊")
st.divider()

# -----------------------------
# Load Knowledge Base (FAQ)
# -----------------------------
def load_faq():
    try:
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, str):
                        data[k] = {"answer": v, "keywords": k.lower().split()}
                return data
    except FileNotFoundError:
        st.info("FAQ file not found. Continuing without FAQs.")
    except json.JSONDecodeError:
        st.warning("FAQ file is not valid JSON. Ignoring FAQ.")
    return {}

faq_data = load_faq()

# -----------------------------
# Find matching FAQ
# -----------------------------
def find_faq(question):
    q = question.lower()
    best = None
    max_hits = 0
    for k, entry in faq_data.items():
        hits = sum(1 for kw in entry.get("keywords", []) if kw in q)
        if hits > max_hits:
            max_hits = hits
            best = entry
    return best if max_hits > 0 else None

# -----------------------------
# Chat session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "introduced" not in st.session_state:
    st.session_state.introduced = False   # Track introduction

# Display chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# -----------------------------
# Chat Input
# -----------------------------
user_input = st.chat_input("Ask Vicky anything about VKIT College...")

if user_input:
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    faq_match = find_faq(user_input)
    context = f"FAQ Answer: {faq_match['answer']}" if faq_match else ""

    # -----------------------------
    # Smart Vicky Prompt Rules
    # -----------------------------
    if not st.session_state.introduced:
        # First response → Vicky introduces herself
        prompt = (
            "Your name is VICKY, the official AI assistant of VKIT College. "
            "You should introduce yourself only once in the first message. "
            "After the first message, NEVER introduce yourself again.\n\n"
            f"Student Question: {user_input}\n"
            f"{context}\n"
            "Give your first answer with introduction:"
        )
        st.session_state.introduced = True
    else:
        # After first message → NO more introduction
        prompt = (
            "You are VICKY, the VKIT College assistant. "
            "You already introduced yourself before. "
            "Do NOT introduce yourself again.\n\n"
            f"Student Question: {user_input}\n"
            f"{context}\n"
            "Answer normally and directly:"
        )

    # -----------------------------
    # Gemini API call
    # -----------------------------
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        bot_reply = response.text.strip()
    except Exception as e:
        bot_reply = f"❌ Gemini API Error: {e}"

    # Show Vicky's response
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

    # Save message
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
