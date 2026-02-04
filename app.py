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
    Renders markdown but extracts triple-backtick code blocks and renders them
    via st.code for nicer formatting + copy button.
    """
    pos = 0
    for m in CODE_BLOCK_RE.finditer(text):
        start, end = m.span()
        lang = (m.group(1) or "").strip()
        code = m.group(2) or ""

        before = text[pos:start]
        if before.strip():
            st.markdown(before, unsafe_allow_html=False)

        st.code(code, language=lang if lang else None)
        pos = end

    rest = text[pos:]
    if rest.strip():
        st.markdown(rest, unsafe_allow_html=False)

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Gemini Chatbot", page_icon="💬", layout="centered")
st.title("💬 Gemini Chatbot")

# -----------------------------
# Simple Login (password gate)
# -----------------------------
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False

def login_ui():
    st.subheader("🔒 تسجيل دخول")
    st.caption("أدخل كلمة السر باش تفتح الشات.")
    pwd = st.text_input("كلمة السر", type="password", placeholder="••••••••••")
    c1, c2 = st.columns([1, 1])
    with c1:
        do_login = st.button("دخول", use_container_width=True)
    with c2:
        st.button("مسح", use_container_width=True, on_click=lambda: None)

    if do_login:
        if APP_PASSWORD and pwd == APP_PASSWORD:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("كلمة السر غلط، أو APP_PASSWORD مش متحطوطة.")

if APP_PASSWORD:
    if not st.session_state.auth_ok:
        login_ui()
        st.stop()
else:
    st.info("⚠️ APP_PASSWORD مش متحطوطة. التطبيق مفتوح بدون تسجيل دخول.")

# -----------------------------
# Sidebar: cleaner layout (no model / no temperature)
# -----------------------------
with st.sidebar:
    st.markdown("### ⚙️ التحكم")

    # أزرار سريعة بشكل أنظف
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 مسح الشات", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with c2:
        if st.button("🚪 خروج", use_container_width=True):
            st.session_state.auth_ok = False
            st.rerun()

    st.divider()

    # System prompt بتصميم أحسن: داخل Expander + نص افتراضي محترم
    with st.expander("🧠 System Prompt", expanded=False):
        st.caption("هذا يوجّه البوت كيف يجاوب. (اختياري)")
        default_prompt = (
            "أنت مساعد مفيد. جاوب بوضوح وباختصار.\n"
            "إذا المستخدم طلب كود، رجّع الكود داخل ``` مع تحديد اللغة.\n"
            "لو المستخدم يكتب باللهجة الليبية، جاوبه باللهجة الليبية."
        )
        system_prompt = st.text_area(
            label="",
            value=st.session_state.get("system_prompt", default_prompt),
            height=140,
            placeholder="اكتب تعليمات للبوت هنا...",
        )
        st.session_state.system_prompt = system_prompt

    st.divider()
    st.caption("Model: gemini-3-flash-preview")

# -----------------------------
# API key (Gemini)
# -----------------------------
API_KEY = os.getenv("GEMINI_API_KEY", "")

if not API_KEY:
    st.error(
        "❌ ما فيش GEMINI_API_KEY.\n\n"
        "✅ حطها في Streamlit Secrets (وقت الاستضافة) أو Environment Variable (محليًا)."
    )
    st.stop()

genai.configure(api_key=API_KEY)

# موديل واحد ثابت حسب طلبك
MODEL_NAME = "gemini-3-flash-preview"

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=st.session_state.get("system_prompt", None),
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
    # Store + show user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        render_markdown_with_codeblocks(user_text)

    # Convert history for Gemini roles: user/model
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

        render_markdown_with_codeblocks(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
