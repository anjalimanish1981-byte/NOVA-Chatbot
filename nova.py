import streamlit as st
from groq import Groq
from tavily import TavilyClient
import datetime
import os

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="NOVA AI Generator",
    page_icon="🤖",
    layout="wide"
)

# ---------------------------------------------------------
# SIDEBAR CONTROLS & SECURE KEY INPUT
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ NOVA Settings")
    
    # Enter key directly in the browser so GitHub scanners cannot revoke it
    groq_api_key = st.text_input(
        "Groq API Key:",
        value=st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", "")),
        type="password",
        placeholder="gsk_...",
        help="Paste your Groq API key here. It remains safe in your browser session."
    )
    
    tavily_api_key = st.text_input(
        "Tavily API Key (Optional):",
        value=st.secrets.get("TAVILY_API_KEY", "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"),
        type="password"
    )

    # Active production chat models on Groq
    model_option = st.selectbox(
        "Select Model:",
        options=[
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b"
        ],
        index=0
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
# CLIENT INITIALIZATION
# ---------------------------------------------------------
groq_client = None
if groq_api_key.strip():
    try:
        groq_client = Groq(api_key=groq_api_key.strip())
    except Exception as e:
        st.sidebar.error(f"Groq Client Error: {e}")

tavily_client = None
if tavily_api_key.strip():
    try:
        tavily_client = TavilyClient(api_key=tavily_api_key.strip())
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
        return "\n".join([f"- {r['content']} (Source: {r['url']})" for r in results.get("results", [])])
    except Exception:
        return ""

def needs_web_search(prompt):
    triggers = ["today", "latest", "current", "news", "price", "weather", "score", "match", "who won", "2025", "2026"]
    return any(t in prompt.lower() for t in triggers)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am NOVA AI. How can I assist you today?"}
    ]

# ---------------------------------------------------------
# MAIN CHAT INTERFACE
# ---------------------------------------------------------
st.title("🤖 NOVA AI Generator")
st.caption(f"Fast AI Assistant powered by Groq (`{model_option}`) with Tavily Web Search")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ask NOVA anything...")

if user_input:
    if not groq_client:
        st.warning("⚠️ Please open the left sidebar (click '>>' at top-left) and enter your Groq API Key.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking & searching..."):
            web_context = search_web(user_input) if needs_web_search(user_input) else ""

            system_prompt = (
                f"You are NOVA, an intelligent AI companion. Tone: {system_tone}. "
                f"Always respond clearly in English unless requested otherwise. Current date: {datetime.date.today()}."
            )
            if web_context:
                system_prompt += f"\nLive Search Context:\n{web_context}"

            payload = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages:
                payload.append({"role": m["role"], "content": m["content"]})

            try:
                response = groq_client.chat.completions.create(
                    messages=payload,
                    model=model_option
                )
                bot_reply = response.choices[0].message.content
            except Exception as e:
                bot_reply = f"⚠️ Error: {e}"

            st.write(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
