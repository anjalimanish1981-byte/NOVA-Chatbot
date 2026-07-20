import streamlit as st
from groq import Groq

st.set_page_config(page_title="NOVA AI", page_icon="🤖")
st.title("NOVA AI Companion")

# Fetch API key securely from Streamlit Secrets
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("Missing Groq API Key! Please set GROQ_API_KEY in Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process user input
if prompt := st.chat_input("Ask NOVA anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Use Groq's fast Llama 3 model
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )
        
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            response_placeholder.markdown(full_response + "▌")
            
        response_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})