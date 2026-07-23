import base64
import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from tavily import TavilyClient

# 1. Page Configuration
st.set_page_config(page_title="NOVA AI", page_icon="🤖", layout="centered")

# --- SIDEBAR THEME CUSTOMIZER ---
st.sidebar.title("🎨 Customizer")
st.sidebar.markdown("Customize NOVA's appearance live:")

# Interactive Color Pickers with defaults
header_color = st.sidebar.color_picker("Header Color", "#1A73E8")
card_bg_color = st.sidebar.color_picker("Card Background", "#F0F4F9")
accent_border = st.sidebar.color_picker("Accent Border", "#E0A96D")
text_color = st.sidebar.color_picker("Card Text Color", "#1F1F1F")

# Quick Preset Shortcuts
st.sidebar.markdown("---")
st.sidebar.subheader("Quick Presets")
preset = st.sidebar.radio(
    "Choose Preset:",
    ["Custom", "Dark Blue & Gold", "Classic Light", "Dark Mode"],
)

if preset == "Dark Blue & Gold":
  header_color = "#E0A96D"
  card_bg_color = "#0D1B2A"
  accent_border = "#E0A96D"
  text_color = "#FFFFFF"
elif preset == "Classic Light":
  header_color = "#1A73E8"
  card_bg_color = "#F0F4F9"
  accent_border = "#1A73E8"
  text_color = "#1F1F1F"
elif preset == "Dark Mode":
  header_color = "#4D94FF"
  card_bg_color = "#1E1E1E"
  accent_border = "#4D94FF"
  text_color = "#F0F0F0"

# Inject Dynamic CSS based on user selections
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
        .welcome-card h2 {{
            color: {header_color};
            margin-top: 0;
        }}
        h1 {{
            color: {header_color} !important;
        }}
    </style>
""",
    unsafe_allow_html=True,
)

# 2. Welcoming Header Banner
st.title("🤖 NOVA AI Companion")

st.markdown(
    """
    <div class="welcome-card">
        <h2>👋 Welcome to NOVA AI!</h2>
        <p>I can help you answer questions, analyze uploaded images, search the live web, or chat!</p>
    </div>
""",
    unsafe_allow_html=True,
)

# 3. Retrieve Secrets & Initialize Clients
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = (
    TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
)


# 4. Helper Functions
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


# 5. Session State Initializations
if "messages" not in st.session_state:
  st.session_state.messages = [
      {
          "role": "assistant",
          "content": (
              "Hello! 👋 I'm NOVA. You can ask me questions, upload images,"
              " or speak using the mic!"
          ),
      }
  ]

# Display Existing Chat History
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 6. Integrated Action Bar
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

# 7. Text Input Bar
typed_prompt = st.chat_input("Ask NOVA anything...")

# Process Input
prompt = spoken_text if spoken_text else typed_prompt

if prompt or uploaded_file:
  active_model = selected_model
  search_context = live_web_search(prompt) if prompt else ""

  sys_msg = (
      "You are NOVA, a helpful AI assistant. Answer accurately.\nWeb Search"
      f" Context:\n{search_context}"
  )

  # Format user content
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

  # Display User Message
  st.session_state.messages.append({"role": "user", "content": display_text})
  with st.chat_message("user"):
    if uploaded_file:
      st.image(uploaded_file, width=250)
    if prompt:
      st.markdown(prompt)

  # Build API Payload
  api_messages = [{"role": "system", "content": sys_msg}]
  for m in st.session_state.messages[:-1]:
    api_messages.append({"role": m["role"], "content": m["content"]})
  api_messages.append({"role": "user", "content": user_content})

  # Call API
  with st.chat_message("assistant"):
    with st.spinner("NOVA is analyzing..."):
      try:
        response = groq_client.chat.completions.create(
            model=active_model, messages=api_messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )
      except Exception as e:
        st.error(f"Error generating response: {e}")
