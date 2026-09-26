import streamlit as st
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
import google.generativeai as genai

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="DMC EMPIRE CHAT BOT",
    page_icon="👑",
    layout="centered"
)

st.title("👑 DMC EMPIRE CHAT BOT")
st.caption("Universal Design • Powered by Prince + Gemini Fallback")

# ──────────────────────────────────────────────
# Load Secrets (from Streamlit Cloud)
# ──────────────────────────────────────────────
try:
    PRINCE_API_KEY = st.secrets["PRINCE_API_KEY"]
    GOOGLE_KEYS = [
        st.secrets.get("GOOGLE_API_KEY_1", ""),
        st.secrets.get("GOOGLE_API_KEY_2", ""),
        st.secrets.get("GOOGLE_API_KEY_3", ""),
    ]
    GOOGLE_KEYS = [k for k in GOOGLE_KEYS if k.strip()]
except Exception:
    st.error("⚠️ Secrets not found. Please add your API keys in Streamlit Secrets.")
    st.stop()

# ──────────────────────────────────────────────
# Session State
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "provider" not in st.session_state:
    st.session_state.provider = "Prince"
if "google_key_index" not in st.session_state:
    st.session_state.google_key_index = 0

# ──────────────────────────────────────────────
# AI Functions
# ──────────────────────────────────────────────
def call_prince(messages):
    client = OpenAI(
        api_key=PRINCE_API_KEY,
        base_url=PRINCE_BASE_URL,
        timeout=25
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",          # Change if Prince uses different model name
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def call_gemini(messages):
    if not GOOGLE_KEYS:
        raise ValueError("No Google API keys available")

    key = GOOGLE_KEYS[st.session_state.google_key_index % len(GOOGLE_KEYS)]
    st.session_state.google_key_index += 1

    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Convert messages for Gemini
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=history)
    response = chat.send_message(messages[-1]["content"])
    return response.text

def get_response(user_input):
    messages = st.session_state.messages + [{"role": "user", "content": user_input}]

    # Try Prince first
    try:
        reply = call_prince(messages)
        return reply, "Prince"
    except Exception:
        st.toast("Prince is offline → Switching to Gemini", icon="⚠️")

    # Fallback to Gemini
    try:
        reply = call_gemini(messages)
        return reply, "Gemini"
    except Exception as e:
        return f"❌ Both systems failed.\n\nError: {e}", "Error"

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("Status")
    st.write(f"**Current AI:** `{st.session_state.provider}`")
    st.write(f"**Google Keys:** {len(GOOGLE_KEYS)}")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ──────────────────────────────────────────────
# Chat Interface
# ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply, provider = get_response(prompt)
            st.session_state.provider = provider
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
