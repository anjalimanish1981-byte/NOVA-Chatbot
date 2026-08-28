import streamlit as st
from groq import Groq
from tavily import TavilyClient
import datetime

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="NOVA AI Generator",
    page_icon="🤖",
    layout="wide"
)

# ---------------------------------------------------------
# API CLIENT INITIALIZATION
# ---------------------------------------------------------
# Replace with your API keys if needed
GROQ_API_KEY = "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"
TAVILY_API_KEY = "tvly-YOUR_TAVILY_API_KEY_HERE"  # Replace with your Tavily key

groq_client = Groq(api_key=GROQ_API_KEY)
try:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
except Exception:
    tavily_client = None

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def search_web(query):
    if not tavily_client:
        return ""
    try:
        results = tavily_client.search(query=query, search_depth="basic", max_results=3)
        context = "\n".join([f"- {r['content']} (Source: {r['url']})" for r in results.get("results", [])])
        return context
    except Exception:
        return ""

def needs_web_search(user_prompt):
    triggers = ["today", "latest", "current", "news", "price", "weather", "score", "match", "who is", "what is happening", "2024", "2025", "2026"]
    return any(t in user_prompt.lower() for t in triggers)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am NOVA AI. How can I assist you today?"}
    ]

# ---------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ NOVA Settings")
    
    model_option = st.selectbox(
        "Select Model:",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    )
    
    system_tone = st.selectbox(
        "AI Personality / Tone:",
        ["Helpful Assistant", "Concise & Direct", "Technical Expert", "Creative Companion"]
    )
    
    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am NOVA AI. How can I assist you today?"}
        ]
        st.rerun()

# ---------------------------------------------------------
# MAIN CHAT INTERFACE
# ---------------------------------------------------------
st.title("🤖 NOVA AI Generator")
st.caption("Fast AI Assistant powered by Groq & LLaMA 3.3")

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Chat Input
user_input = st.chat_input("Ask NOVA anything...")

if user_input:
    # Append & display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            web_context = ""
            if needs_web_search(user_input):
                web_context = search_web(user_input)

            system_prompt = (
                f"You are NOVA, a smart, versatile AI companion. Tone: {system_tone}. "
                f"Current date: {datetime.date.today()}. "
            )
            if web_context:
                system_prompt += f"\nRelevant web search results:\n{web_context}\nUse this live information to answer accurately."

            messages_payload = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages:
                messages_payload.append({"role": m["role"], "content": m["content"]})

            try:
                response = groq_client.chat.completions.create(
                    messages=messages_payload,
                    model=model_option
                )
                bot_reply = response.choices[0].message.content
            except Exception as e:
                bot_reply = f"⚠️ Error: {e}"

            st.write(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})


