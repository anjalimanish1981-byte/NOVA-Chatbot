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
# SIDEBAR CONTROLS & SECURE CREDENTIAL FALLBACK
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ NOVA Settings")
    
    # Reads securely from Streamlit Secrets or sidebar entry
    groq_api_key = st.text_input(
        "Groq API Key:",
        value=st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", "")),
        type="password",
        placeholder="gsk_...",
        help="Reads automatically from Streamlit Secrets if configured."
    )
    
    tavily_api_key = st.text_input(
        "Tavily API Key (Optional):",
        value=st.secrets.get("TAVILY_API_KEY", "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"),
        type="password"
    )

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
# TARGETED WEB SEARCH ENGINE
# ---------------------------------------------------------
def search_web(query):
    if not tavily_client:
        return ""
    try:
        search_query = query
        # Enhance sports queries to pull exact post-match scorecards
        if any(term in query.lower() for term in ["match", "who won", "score", "vs", "cup", "t20", "odi", "test", "result"]):
            search_query += " cricket full scorecard final result playing XI"

        results = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5
        )
        snippets = []
        for r in results.get("results", []):
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")
            snippets.append(f"Source: {title} ({url})\n{content}")
        return "\n\n---\n\n".join(snippets)
    except Exception:
        return ""

def needs_web_search(prompt):
    triggers = [
        "today", "latest", "current", "news", "price", "weather", 
        "score", "match", "who won", "who is", "what is happening", 
        "vs", "odi", "t20", "test", "final", "series", "2025", "2026"
    ]
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
        st.warning("⚠️ Please enter your Groq API Key in the left sidebar to start chatting.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing facts & searching real-time context..."):
            web_context = search_web(user_input) if needs_web_search(user_input) else ""

            # Strict anti-hallucination system prompt
            system_prompt = (
                f"You are NOVA, a reliable, grounded, and helpful AI assistant. Tone: {system_tone}.\n"
                f"Current Date: {datetime.date.today()}.\n\n"
                "STRICT FACTUAL ACCURACY RULES:\n"
                "1. Base all facts, scores, dates, and sports events EXCLUSIVELY on the provided LIVE WEB SEARCH RESULTS.\n"
                "2. NEVER swap players between opposing teams (e.g., ensure players are listed strictly under their actual nation).\n"
                "3. If the search results do not provide the final score or result, clearly state: "
                "'The match details or final result could not be fully verified from live sources.' Do not invent numbers, overs, or wickets.\n"
                "4. When a verified match summary is available, format cleanly using:\n"
                "   - Match title, date, venue, and toss.\n"
                "   - A Markdown table showing Team, Score / Overs, and top performers.\n"
                "   - Player of the Match and key highlights.\n"
            )

            if web_context:
                system_prompt += f"\nLIVE WEB SEARCH RESULTS:\n{web_context}\n"

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
