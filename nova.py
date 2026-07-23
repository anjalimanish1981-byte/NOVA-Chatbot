import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text
from tavily import TavilyClient

# 1. Page Configuration
st.set_page_config(page_title="NOVA AI", page_icon="🤖", layout="centered")

# Custom Styling for Welcoming UI
st.markdown(
    """
    <style>
        .welcome-card {
            background-color: #f0f4f9;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            border-left: 5px solid #1a73e8;
        }
        .welcome-card h2 {
            color: #1a73e8;
            margin-top: 0;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# 2. Welcoming Header & Banner
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


# 5. Session State for Chat History
if "messages" not in st.session_state:
  st.session_state.messages = [
      {
          "role": "assistant",
          "content": (
              "Hello! 👋 I'm NOVA. How can I assist you today? You can type"
              " your question or click the microphone button below to speak!"
          ),
      }
  ]

# Display Existing Chat Messages
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 6. Voice Input Section
st.write("🎙️ **Voice Input:**")
spoken_text = speech_to_text(
    language="en",
    start_prompt="Tap to Speak 🎤",
    stop_prompt="Stop Recording ⏹️",
    just_once=True,
    key="voice_input",
)

# 7. Text Input Section
typed_prompt = st.chat_input("Ask NOVA anything...")

# Determine Prompt Source (Voice or Text)
prompt = None
if spoken_text:
  prompt = spoken_text
elif typed_prompt:
  prompt = typed_prompt

# 8. Process Prompt & Generate AI Response
if prompt:
  # Append & Display User Message
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  # Perform Live Web Search
  search_context = live_web_search(prompt)

  # Build System Prompt
  system_prompt = (
      "You are NOVA, a friendly and helpful AI assistant with real-time web"
      " search access.\nUse the provided Web Search Context below when"
      " relevant.\n\nWeb Search Context:\n"
      f"{search_context}"
  )

  messages_payload = [{"role": "system", "content": system_prompt}] + [
      {"role": m["role"], "content": m["content"]}
      for m in st.session_state.messages
  ]

  # Generate AI Response from Groq
  with st.chat_message("assistant"):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", messages=messages_payload
    )
    reply = response.choices[0].message.content
    st.markdown(reply)

  # Append Assistant Response
  st.session_state.messages.append({"role": "assistant", "content": reply})
