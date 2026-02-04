import os
import re
import streamlit as st
import google.generativeai as genai

# -----------------------------
# Helpers: Markdown + code blocks rendering
# -----------------------------
CODE_BLOCK_RE = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

def render_markdown_with_codeblocks(text: str):
    """
    Renders markdown text but extracts triple-backtick code blocks and renders them
    using st.code (gives nicer formatting + built-in copy button in Streamlit).
    The rest is rendered via st.markdown.
    """
    pos = 0
    for m in CODE_BLOCK_RE.finditer(text):
        start, end = m.span()
        lang = (m.group(1) or "").strip()
        code = m.group(2) or ""

        # markdown before codeblock
        before = text[pos:start]
        if before.strip():
            st.markdown(before, unsafe_allow_html=False)

        # codeblock
        st.code(code, language=lang if lang else None)

        pos = end

    # remaining markdown
    rest = text[pos:]
    if rest.strip():
        st.markdown(rest, unsafe_allow_html=False)

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Gemini Chatbot", page_icon="💬", layout="centered")
st.title("💬 Gemini Chatbot (Streamlit)")

# -----------------------------
# Simple Login (password gate)
# -----------------------------
# Put this in Streamlit Secrets or environment variable:
# APP_PASSWORD = "your_password"
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False

def login_ui():
    st.subheader("🔒 تسجيل دخول")
    st.caption("أدخل كلمة السر باش تفتح الشات.")
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if APP_PASSWORD and pwd == APP_PASSWORD:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("كلمة السر غلط، أو APP_PASSWORD مش متحطوطة.")

# إذا ما فيش باسورد أصلاً، نعتبره مفتوح (اختياري)
# لكن الأفضل تحط باسورد.
if APP_PASSWORD:
    if not st.session_state.auth_ok:
        login_ui()
        st.stop()
else:
    st.info("⚠️ APP_PASSWORD مش متحطوطة. التطبيق مفتوح بدون تسجيل دخول.")

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.header("⚙️ الإعدادات")

    model_name = st.selectbox(
        "اختار الموديل",
        ["gemini-3-flash-preview", "gemini-1.5-pro"],
        index=0,
    )

    temperature = st.slider("Temperature (إبداع الرد)", 0.0, 1.0, 0.5, 0.1)

    system_prompt = st.text_area(
        "System Prompt (اختياري)",
        value="أنت مساعد مفيد. لما المستخدم يطلب كود، رجّع الكود داخل ثلاث backticks ``` مع تحديد اللغة.",
        height=110,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 مسح المحادثة", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    with col2:
        if st.button("🚪 خروج", use_container_width=True):
            st.session_state.auth_ok = False
            st.rerun()

# -----------------------------
# API key (Gemini)
# -----------------------------
# Put this in Streamlit Secrets or environment variable:
# GEMINI_API_KEY = "your_key"
API_KEY = os.getenv("GEMINI_API_KEY", "")

if not API_KEY:
    st.error(
        "❌ ما فيش GEMINI_API_KEY.\n\n"
        "✅ حطها في Streamlit Secrets (وقت الاستضافة) أو Environment Variable (محليًا)."
    )
    st.stop()

genai.configure(api_key=API_KEY)

generation_config = genai.types.GenerationConfig(
    temperature=temperature,
)

model = genai.GenerativeModel(
    model_name=model_name,
    generation_config=generation_config,
    system_instruction=system_prompt if system_prompt.strip() else None,
)

# -----------------------------
# Session messages
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# Render chat history
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_markdown_with_codeblocks(msg["content"])

# -----------------------------
# Chat input
# -----------------------------
user_text = st.chat_input("اكتب رسالتك هنا...")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        render_markdown_with_codeblocks(user_text)

    # Convert history for Gemini roles: user/model
    history = []
    for m in st.session_state.messages[:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    with st.chat_message("assistant"):
        with st.spinner("⏳ نستنى في رد Gemini..."):
            try:
                chat = model.start_chat(history=history)
                resp = chat.send_message(user_text)
                answer = resp.text if hasattr(resp, "text") else "ما قدرتش نجيب رد."
            except Exception as e:
                answer = f"صار خطأ: {e}"

        render_markdown_with_codeblocks(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

