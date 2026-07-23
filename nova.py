import base64
import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from tavily import TavilyClient

# 1. Page Configuration & CSS
st.set_page_config(page_title="NOVA AI", page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
        .welcome-card {
            background-color: #f0f4f9;
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 25px;
            border-left: 5px solid #1a73e8;
            font-family: sans-serif;
        }
        .welcome-card h2 {
            color: #1a73e8;
            margin-top: 0;
        }
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


# 4. Helper: Base64 Encoding
def encode_image(file):
  return base64.b64encode(file.getvalue()).decode("utf-8")


# 5. Helper: Web Search
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


# 6. Session State Initializations
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

# 7. Controls Top Bar
st.write("---")
col_attach, col_model, col_voice = st.columns([2, 3, 2])

with col_attach:
  uploaded_file = st.file_uploader(
      "Attach Image",
      type=["png", "jpg", "jpeg", "webp"],
      label_visibility="collapsed",
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

# 8. Bottom Chat Input
typed_prompt = st.chat_input("Ask NOVA anything...")

# Determine Input Source
prompt = spoken_text if spoken_text else typed_prompt

if prompt or uploaded_file:
  active_model = selected_model
  search_context = live_web_search(prompt) if prompt else ""

  # System Message
  sys_msg = (
      "You are NOVA, a helpful AI assistant. Answer accurately.\nWeb Search"
      f" Context:\n{search_context}"
  )

  # Format user content
  if uploaded_file is not None:
    # Use Groq's multimodal Qwen vision model for image processing
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

  # Append and Display User Message
  st.session_state.messages.append({"role": "user", "content": display_text})
  with st.chat_message("user"):
    if uploaded_file:
      st.image(uploaded_file, width=250)
    if prompt:
      st.markdown(prompt)

  # Build Clean API Payload
  api_messages = [{"role": "system", "content": sys_msg}]

  # Add prior history as plain text strings
  for m in st.session_state.messages[:-1]:
    api_messages.append({"role": m["role"], "content": m["content"]})

  # Add current query payload
  api_messages.append({"role": "user", "content": user_content})

  # Call Groq API
  with st.chat_message("assistant"):
    with st.spinner("NOVA is analyzing..."):
      try:
        response = groq_client.chat.completions.create(
            model=active_model, messages=api_messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)

        # Save Assistant Reply
        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )
      except Exception as e:
        st.error(f"Error generating response: {e}")
