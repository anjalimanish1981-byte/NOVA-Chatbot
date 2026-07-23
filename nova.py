import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from tavily import TavilyClient

# 1. Page Configuration & Custom CSS Styling
st.set_page_config(page_title="NOVA AI", page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
        /* Card styling for welcome message */
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
        
        /* Custom styling for bottom bar container */
        .stSelectbox div[data-baseweb="select"] {
            border-radius: 20px;
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
        <p>I can help you answer questions, search the live web for recent updates, or chat about anything you like.</p>
        <p><b>Try asking:</b></p>
        <ul>
            <li>"What is the current weather in Mumbai?"</li>
            <li>"Who won the last India vs England cricket match?"</li>
            <li>"What are today's top headlines?"</li>
        </ul>
    </div>
""",
    unsafe_allow_html=True,
)

# 3. Retrieve API Keys from Streamlit Secrets
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")

# Initialize Clients
groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = (
    TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
)


# 4. Live Web Search Function
def live_web_search(query):
  if not tavily_client:
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
              "Hello! 👋 I'm NOVA. How can I assist you today? You can type,"
              " speak, or upload files!"
          ),
      }
  ]

# Display Chat History
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])


# 6. Action Bar (Attachment +, Model Selector, and Voice Mic)
st.write("---")
col_attach, col_model, col_voice = st.columns([1, 3, 2])

with col_attach:
  uploaded_file = st.file_uploader(
      "Attach", type=["txt", "pdf", "csv", "png", "jpg"], label_visibility="collapsed"
  )

with col_model:
  selected_model = st.selectbox(
      "Model",
      ["llama-3.3-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768"],
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

# 7. Bottom Text Input Bar
typed_prompt = st.chat_input("Ask NOVA anything...")

# Process Input
prompt = None
if spoken_text:
  prompt = spoken_text
elif typed_prompt:
  prompt = typed_prompt

# Process File Contents if uploaded
file_context = ""
if uploaded_file is not None:
  file_context = f"\n\n[Uploaded File Content ({uploaded_file.name}) Attached]"

if prompt:
  full_user_prompt = prompt + (
      f" (Attached file: {uploaded_file.name})" if uploaded_file else ""
  )

  # Append & Display User Message
  st.session_state.messages.append(
      {"role": "user", "content": full_user_prompt}
  )
  with st.chat_message("user"):
    st.markdown(full_user_prompt)

  # Perform Search
  search_context = live_web_search(prompt)

  # System Context
  system_prompt = (
      "You are NOVA, a helpful AI assistant with real-time web search access.\n"
      f"Web Search Context:\n{search_context}{file_context}"
  )

  messages_payload = [{"role": "system", "content": system_prompt}] + [
      {"role": m["role"], "content": m["content"]}
      for m in st.session_state.messages
  ]

  # Generate Response
  with st.chat_message("assistant"):
    response = groq_client.chat.completions.create(
        model=selected_model, messages=messages_payload
    )
    reply = response.choices[0].message.content
    st.markdown(reply)

  # Append Assistant Response
  st.session_state.messages.append({"role": "assistant", "content": reply})
