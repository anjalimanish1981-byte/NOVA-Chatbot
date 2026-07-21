import os
import requests
import streamlit as st
from groq import Groq

# 1. Page Configuration
st.set_page_config(page_title="NOVA AI", page_icon="🤖")
st.title("NOVA AI Companion")

# 2. Retrieve Secrets from Streamlit Secrets
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = st.secrets.get("GOOGLE_CSE_ID")

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)


# 3. Google Custom Search Function
def google_search(query):
  if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    return ""
  url = "https://www.googleapis.com/customsearch/v1"
  params = {"q": query, "key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID, "num": 3}
  try:
    response = requests.get(url, params=params)
    data = response.json()
    results = data.get("items", [])
    search_summary = "\n".join(
        [f"- {item.get('title')}: {item.get('snippet')}" for item in results]
    )
    return search_summary
  except Exception:
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

  # Perform Google Search for context
  search_context = google_search(prompt)

  # Build System Prompt with Live Search Context
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