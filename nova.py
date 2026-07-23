import base64
import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from supabase import create_client
from tavily import TavilyClient

# 1. Page Configuration
st.set_page_config(page_title="NOVA AI", page_icon="🤖", layout="centered")

# --- SUPABASE & API INITIALIZATION ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = (
    TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
)


@st.cache_resource
def init_supabase():
  if SUPABASE_URL and SUPABASE_KEY:
    return create_client(SUPABASE_URL, SUPABASE_KEY)
  return None


supabase = init_supabase()

# --- AUTHENTICATION STATE ---
if "user_email" not in st.session_state:
  st.session_state.user_email = None
if "user_name" not in st.session_state:
  st.session_state.user_name = ""
if "otp_sent" not in st.session_state:
  st.session_state.otp_sent = False


# --- SIGN IN & SIGN UP SCREEN ---
def login_screen():
  st.title("🔐 Welcome to NOVA AI")
  st.markdown("Sign in with your email and name to get started!")

  with st.form("otp_login_form"):
    user_name_input = st.text_input("Your Name:", placeholder="e.g. Anjali")
    email_input = st.text_input(
        "Your Email Address:", placeholder="name@example.com"
    )
    submit_email = st.form_submit_button("Send OTP Code 📩")

    if submit_email and email_input:
      st.session_state.user_name = (
          user_name_input.strip()
          if user_name_input.strip()
          else email_input.split("@")[0].capitalize()
      )
      st.session_state.user_email = email_input.strip()

      if supabase:
        try:
          supabase.auth.sign_in_with_otp({"email": email_input.strip()})
          st.session_state.otp_sent = True
          st.success(
              f"OTP code sent to **{email_input}**! Please check your inbox."
          )
        except Exception as e:
          st.error(f"Error sending OTP: {e}")
      else:
        st.session_state.otp_sent = True
        st.info("Demo Mode: Enter any 6-digit OTP code below to sign in.")

  if st.session_state.otp_sent:
    with st.form("verify_otp_form"):
      otp_code = st.text_input(
          "Enter 6-digit OTP Code:",
          type="password",
          placeholder="Check your email",
      )
      verify_btn = st.form_submit_button("Verify & Sign In 🚀")

      if verify_btn and otp_code:
        if supabase:
          try:
            res = supabase.auth.verify_otp({
                "email": st.session_state.user_email,
                "token": otp_code,
                "type": "email",
            })
            if res.user:
              st.success(f"Welcome, {st.session_state.user_name}!")
              st.rerun()
          except Exception:
            st.error("Invalid or expired OTP code. Please try again.")
        else:
          # Demo login fallback
          st.rerun()


# --- CHECK LOGGED IN STATUS ---
if not st.session_state.user_email or not st.session_state.otp_sent:
  login_screen()
  st.stop()  # Halt execution until authenticated

# --- MAIN APP ONCE SIGNED IN ---

# Session state for chats
if "chats" not in st.session_state:
  st.session_state.chats = {
      "chat_1": {
          "title": "Welcome Chat",
          "messages": [{
              "role": "assistant",
              "content": (
                  f"Hello **{st.session_state.user_name}**! 👋 I'm NOVA. How"
                  " can I assist you today?"
              ),
          }],
      }
  }

if "active_chat_id" not in st.session_state:
  st.session_state.active_chat_id = "chat_1"


def create_new_chat():
  new_id = f"chat_{len(st.session_state.chats) + 1}"
  st.session_state.chats[new_id] = {
      "title": f"New Chat {len(st.session_state.chats) + 1}",
      "messages": [{
          "role": "assistant",
          "content": (
              f"Hello **{st.session_state.user_name}**! 👋 How can I help you"
              " in this new conversation?"
          ),
      }],
  }
  st.session_state.active_chat_id = new_id


def logout():
  st.session_state.user_email = None
  st.session_state.user_name = ""
  st.session_state.otp_sent = False
  st.rerun()


# --- SIDEBAR: USER INFO & CONTROLS ---
st.sidebar.markdown(f"👋 **Welcome, {st.session_state.user_name}!**")
st.sidebar.caption(f"📧 `{st.session_state.user_email}`")
st.sidebar.button("🚪 Log Out", on_click=logout)
st.sidebar.markdown("---")

st.sidebar.title("🎨 Customizer")
preset = st.sidebar.radio(
    "Choose Preset:",
    ["Custom", "Dark Blue & Gold", "Classic Light", "Dark Mode"],
)

if preset == "Dark Blue & Gold":
  header_color, card_bg_color, accent_border, text_color = (
      "#E0A96D",
      "#0D1B2A",
      "#E0A96D",
      "#FFFFFF",
  )
elif preset == "Classic Light":
  header_color, card_bg_color, accent_border, text_color = (
      "#1A73E8",
      "#F0F4F9",
      "#1A73E8",
      "#1F1F1F",
  )
elif preset == "Dark Mode":
  header_color, card_bg_color, accent_border, text_color = (
      "#4D94FF",
      "#1E1E1E",
      "#4D94FF",
      "#F0F0F0",
  )
else:
  header_color = st.sidebar.color_picker("Header Color", "#1A73E8")
  card_bg_color = st.sidebar.color_picker("Card Background", "#F0F4F9")
  accent_border = st.sidebar.color_picker("Accent Border", "#E0A96D")
  text_color = st.sidebar.color_picker("Card Text Color", "#1F1F1F")

st.sidebar.markdown("---")
st.sidebar.button(
    "➕ New Chat", on_click=create_new_chat, use_container_width=True
)

st.sidebar.markdown("### 🕒 Recent Chats")
for chat_id, chat_data in list(st.session_state.chats.items())[::-1]:
  btn_type = (
      "primary" if chat_id == st.session_state.active_chat_id else "secondary"
  )
  if st.sidebar.button(
      chat_data["title"],
      key=chat_id,
      use_container_width=True,
      type=btn_type,
  ):
    st.session_state.active_chat_id = chat_id
    st.rerun()

# Dynamic Styling Injection
st.markdown(
    f"""
    <style>
        .welcome-card {{
            background-color: {card_bg_color};
            color: {text_color};
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 20px;
            border-left: 6px solid {accent_border};
            font-family: sans-serif;
        }}
        .welcome-card h2 {{ color: {header_color}; margin-top: 0; }}
        h1 {{ color: {header_color} !important; }}
    </style>
""",
    unsafe_allow_html=True,
)

# Header Banner with Personal Greeting
st.title("🤖 NOVA AI Companion")
st.markdown(
    f"""
    <div class="welcome-card">
        <h2>👋 Welcome, {st.session_state.user_name}!</h2>
        <p>I'm your AI companion. I can help answer questions, analyze uploaded images, search the live web, or chat with you!</p>
    </div>
""",
    unsafe_allow_html=True,
)


# Helper Functions
def encode_image(file):
  return base64.b64encode(file.getvalue()).decode("utf-8")


def live_web_search(query):
  if not tavily_client or not query:
    return ""
  try:
    response = tavily_client.search(query=query, max_results=3)
    results = []
    for r in response.get("results", []):
      results.append(f"- {r.get('title')}: {r.get('content')}")
    return "\n".join(results)
  except Exception:
    return ""


# Active Messages Rendering
current_chat = st.session_state.chats[st.session_state.active_chat_id]
active_messages = current_chat["messages"]

for message in active_messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Bottom Input Toolbar
st.write("")
col_attach, col_model, col_voice = st.columns([1, 2, 1])

with col_attach:
  uploaded_file = st.file_uploader(
      "➕ Image",
      type=["png", "jpg", "jpeg", "webp"],
      label_visibility="collapsed",
      key="file_attach",
  )

with col_model:
  selected_model = st.selectbox(
      "Model",
      [
          "llama-3.3-70b-versatile",
          "llama-3.1-8b-instant",
          "qwen/qwen3.6-27b",
      ],
      label_visibility="collapsed",
  )

with col_voice:
  spoken_text = speech_to_text(
      language="en",
      start_prompt="🎙️ Speak",
      stop_prompt="⏹️ Stop",
      just_once=True,
      key="voice_input",
  )

typed_prompt = st.chat_input("Ask NOVA anything...")
prompt = spoken_text if spoken_text else typed_prompt

if prompt or uploaded_file:
  active_model = selected_model
  search_context = live_web_search(prompt) if prompt else ""

  if len(active_messages) <= 1 and prompt:
    current_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

  sys_msg = (
      f"You are NOVA, a helpful AI assistant speaking with"
      f" {st.session_state.user_name}.\nWeb Search Context:\n{search_context}"
  )

  if uploaded_file is not None:
    active_model = "qwen/qwen3.6-27b"
    base64_img = encode_image(uploaded_file)
    mime_type = uploaded_file.type

    user_content = [
        {
            "type": "text",
            "text": prompt if prompt else "What is in this image?",
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_img}"},
        },
    ]
    display_text = (
        prompt
        if prompt
        else f"🖼️ *Uploaded Image ({uploaded_file.name}) for analysis*"
    )
  else:
    user_content = prompt
    display_text = prompt

  active_messages.append({"role": "user", "content": display_text})
  with st.chat_message("user"):
    if uploaded_file:
      st.image(uploaded_file, width=250)
    if prompt:
      st.markdown(prompt)

  api_messages = [{"role": "system", "content": sys_msg}]
  for m in active_messages[:-1]:
    api_messages.append({"role": m["role"], "content": m["content"]})
  api_messages.append({"role": "user", "content": user_content})

  with st.chat_message("assistant"):
    with st.spinner("NOVA is analyzing..."):
      try:
        response = groq_client.chat.completions.create(
            model=active_model, messages=api_messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        active_messages.append({"role": "assistant", "content": reply})
      except Exception as e:
        st.error(f"Error generating response: {e}")
