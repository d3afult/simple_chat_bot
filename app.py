import os
import streamlit as st
import google.generativeai as genai

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Gemini Chatbot", page_icon="💬", layout="centered")
st.title("💬 Gemini Chatbot (Streamlit)")

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.header("⚙️ الإعدادات")

    model_name = st.selectbox(
        "اختار الموديل",
        [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        index=0,
    )

    temperature = st.slider("Temperature (إبداع الرد)", 0.0, 1.0, 0.5, 0.1)

    system_prompt = st.text_area(
        "System Prompt (اختياري)",
        value="أنت مساعد مفيد وتجاوب باللهجة الليبية لو يطلب المستخدم.",
        height=90,
    )

    if st.button("🧹 مسح المحادثة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -----------------------------
# API key
# -----------------------------
# Reads from environment variable or Streamlit Secrets (when deployed).
API_KEY = os.getenv("AIzaSyDtm-GNk_d1BQNg7XQht9GgbI4rWz3cE8w", "")

if not API_KEY:
    st.error(
        "❌ ما فيش API Key.\n\n"
        "✅ حط `GEMINI_API_KEY` في Streamlit Secrets (وقت الاستضافة) "
        "أو كـ Environment Variable (وقت التشغيل محليًا)."
    )
    st.stop()

genai.configure(api_key=API_KEY)

# -----------------------------
# Build model (with generation config)
# -----------------------------
generation_config = genai.types.GenerationConfig(
    temperature=temperature,
)

model = genai.GenerativeModel(
    model_name=model_name,
    generation_config=generation_config,
    system_instruction=system_prompt if system_prompt.strip() else None,
)

# -----------------------------
# Session state: messages
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# Render chat history
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# Chat input
# -----------------------------
user_text = st.chat_input("اكتب رسالتك هنا...")

if user_text:
    # show and store user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Prepare history for Gemini
    # Gemini expects roles: "user" and "model"
    history = []
    for m in st.session_state.messages[:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("⏳ نستنى في رد Gemini..."):
            try:
                chat = model.start_chat(history=history)
                resp = chat.send_message(user_text)
                answer = resp.text if hasattr(resp, "text") else "ما قدرتش نجيب رد."

            except Exception as e:
                answer = f"صار خطأ: {e}"

        st.markdown(answer)

    # store assistant message
    st.session_state.messages.append({"role": "assistant", "content": answer})
