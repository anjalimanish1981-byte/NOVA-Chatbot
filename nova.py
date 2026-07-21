import streamlit as st
from groq import Groq
from tavily import TavilyClient

# 1. Page Configuration
st.set_page_config(page_title="NOVA AI", page_icon="🤖")
st.title("NOVA AI Companion")

# 2. Retrieve API Keys from Streamlit Secrets
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")

# Initialize Clients
groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = (
    TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
)


# 3. Live Web Search via Tavily API
def live_web_search(query):
  if not tavily_client:
    return ""
  try:
    response = tavily_client.search(query=query, max_results=3)
    results = []
    for r in response.get("results", []):
      results.append(f"- {r.get('title')}: {r.get('content')}")
    return "\n".join(results)
  except Exception as e:
    return ""


# 4. Session State for Chat History
if "messages" not in st.session_state:
  st.session_state.messages = []

# Display Existing Chat Messages
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 5. Handle User Input
if prompt := st.chat_input("Ask NOVA anything..."):
  # Append & Display User Message
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  # Perform Live Search
  search_context = live_web_search(prompt)

  # Build System Prompt with Live Context
  system_prompt = (
      "You are NOVA, a helpful AI assistant with access to real-time search context.\n"
      "Use the provided Web Search Context below to answer the user's question accurately.\n\n"
      f"Web Search Context:\n{search_context}"
  )

  messages_payload = [{"role": "system", "content": system_prompt}] + [
      {"role": m["role"], "content": m["content"]}
      for m in st.session_state.messages
  ]

  # Generate Response from Groq
  with st.chat_message("assistant"):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile", messages=messages_payload
    )
    reply = response.choices[0].message.content
    st.markdown(reply)

  # Append Assistant Response to Chat
  st.session_state.messages.append({"role": "assistant", "content": reply})
