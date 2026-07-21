import streamlit as st
from duckduckgo_search import DDGS
from groq import Groq

# 1. Page Configuration
st.set_page_config(page_title="NOVA AI", page_icon="🤖")
st.title("NOVA AI Companion")

# 2. Retrieve Groq API Key from Streamlit Secrets
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)


# 3. Reliable Web Search Function using duckduckgo-search package
def live_web_search(query):
  try:
    results = []
    with DDGS() as ddgs:
      for r in ddgs.text(query, max_results=3):
        results.append(f"- {r.get('title')}: {r.get('body')}")
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
      "You are NOVA, a helpful AI assistant. "
      "Use the provided web search context to answer accurately if relevant.\n\n"
      f"Web Search Context:\n{search_context}"
  )

  messages_payload = [{"role": "system", "content": system_prompt}] + [
      {"role": m["role"], "content": m["content"]}
      for m in st.session_state.messages
  ]

  # Generate Response from Groq
  with st.chat_message("assistant"):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", messages=messages_payload
    )
    reply = response.choices[0].message.content
    st.markdown(reply)

  # Append Assistant Response to Chat
  st.session_state.messages.append({"role": "assistant", "content": reply})
