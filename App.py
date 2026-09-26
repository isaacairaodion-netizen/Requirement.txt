import streamlit as st
import requests
import google.generativeai as genai

# ──────────────────────────────────────────────
# Page Setup
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="DMC EMPIRE CHAT BOT",
    page_icon="👑",
    layout="centered"
)

st.title("👑 DMC EMPIRE CHAT BOT")
st.caption("Universal Design")


# ──────────────────────────────────────────────
# Secrets
# ──────────────────────────────────────────────
try:
    PRINCE_API_KEY = st.secrets.get("PRINCE_API_KEY", "")

    GOOGLE_KEYS = [
        st.secrets.get("GOOGLE_API_KEY_1", ""),
        st.secrets.get("GOOGLE_API_KEY_2", ""),
        st.secrets.get("GOOGLE_API_KEY_3", ""),
    ]

    GOOGLE_KEYS = [k.strip() for k in GOOGLE_KEYS if k.strip()]

except Exception:
    st.error("⚠️ Please configure your Streamlit Secrets.")
    st.stop()


# ──────────────────────────────────────────────
# Session State
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "provider" not in st.session_state:
    st.session_state.provider = "—"

if "google_key_index" not in st.session_state:
    st.session_state.google_key_index = 0


# ──────────────────────────────────────────────
# PRINCE API
# ──────────────────────────────────────────────
def call_prince(messages):

    if not PRINCE_API_KEY:
        raise ValueError("PRINCE API key is not configured.")

    # Set your actual PRINCE API endpoint here.
    # This is intentionally separate from the API key.
    PRINCE_API_URL = "YOUR_PRINCE_API_ENDPOINT"

    payload = {
        "messages": messages,
        "prm": True
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PRINCE_API_KEY}"
    }

    response = requests.post(
        PRINCE_API_URL,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    # Accept common PRINCE response formats
    if "reply" in data:
        return data["reply"]

    if "response" in data:
        return data["response"]

    if "message" in data:
        return data["message"]

    if "content" in data:
        return data["content"]

    raise ValueError(
        f"Unknown PRINCE API response: {data}"
    )


# ──────────────────────────────────────────────
# Gemini Fallback
# ──────────────────────────────────────────────
def call_gemini(messages):

    if not GOOGLE_KEYS:
        raise ValueError("No Google API keys found.")

    key = GOOGLE_KEYS[
        st.session_state.google_key_index
        % len(GOOGLE_KEYS)
    ]

    st.session_state.google_key_index += 1

    genai.configure(api_key=key)

    model = genai.GenerativeModel(
        "gemini-1.5-flash"
    )

    history = []

    for msg in messages[:-1]:

        role = (
            "user"
            if msg["role"] == "user"
            else "model"
        )

        history.append({
            "role": role,
            "parts": [msg["content"]]
        })

    chat = model.start_chat(
        history=history
    )

    response = chat.send_message(
        messages[-1]["content"]
    )

    return response.text


# ──────────────────────────────────────────────
# AI Router
# ──────────────────────────────────────────────
def get_response(user_input):

    messages = (
        st.session_state.messages
        + [{
            "role": "user",
            "content": user_input
        }]
    )

    # PRINCE FIRST
    try:

        reply = call_prince(messages)

        return reply, "PRINCE"

    except Exception as e:

        st.toast(
            "PRINCE unavailable → Gemini fallback",
            icon="⚠️"
        )

    # Gemini fallback
    try:

        reply = call_gemini(messages)

        return reply, "Gemini"

    except Exception as e:

        return (
            f"❌ AI Error: {e}",
            "Error"
        )


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:

    st.header("👑 PRINCE SYSTEM")

    st.write(
        f"**Current AI:** `{st.session_state.provider}`"
    )

    st.write(
        f"**Google Keys:** `{len(GOOGLE_KEYS)}`"
    )

    if PRINCE_API_KEY:
        st.success("PRINCE API KEY: LOADED")
    else:
        st.warning("PRINCE API KEY: MISSING")

    st.divider()

    if st.button("🗑️ Clear Chat"):

        st.session_state.messages = []

        st.rerun()


# ──────────────────────────────────────────────
# Chat History
# ──────────────────────────────────────────────
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])


# ──────────────────────────────────────────────
# Chat Input
# ──────────────────────────────────────────────
if prompt := st.chat_input("Talk to PRINCE..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("PRINCE is thinking..."):

            reply, provider = get_response(prompt)

            st.session_state.provider = provider

            st.markdown(reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })
