 import os
import requests
import streamlit as st
from bs4 import BeautifulSoup
from groq import Groq

# 1. Page Configuration
st.set_page_config(page_title="NOVA AI", page_icon="🤖")
st.title("NOVA AI Companion")

# 2. Retrieve Groq API Key from Streamlit Secrets
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)


# 3. Free Web Search Function (DuckDuckGo API)
def live_web_search(query):
  try:
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    response = requests.post(url, data={"q": query}, headers=headers, timeout=5)

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for snippet in soup.find_all("a", class_="result__snippet")[:3]:
      results.append(f"- {snippet.get_text().strip()}")

    return "\n".join(results)
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