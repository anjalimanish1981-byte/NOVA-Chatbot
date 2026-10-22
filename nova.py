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
# SIDEBAR CONTROLS & API KEYS
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ NOVA Settings")
    
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
# ENHANCED WEB SEARCH ENGINE
# ---------------------------------------------------------
def search_web(query):
    if not tavily_client:
        return ""
    try:
        # Optimized query targeting completed scores and final results
        search_query = query
        if any(term in query.lower() for term in ["match", "who won", "score", "vs", "cup", "t20", "odi", "test"]):
            search_query += " full scorecard final match result winner"

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
    except Exception as e:
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
        st.warning("⚠️ Please open the sidebar and enter your Groq API Key.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Searching real-time data & generating match card..."):
            web_context = search_web(user_input) if needs_web_search(user_input) else ""

            # Structured prompt instructing NOVA to output formatted tables & highlights
            system_prompt = (
                f"You are NOVA, an advanced AI collaborator. Tone: {system_tone}.\n"
                f"Current Date: {datetime.date.today()}.\n"
                "IMPORTANT RESPONSE FORMATTING RULES:\n"
                "1. If answering a sports, match, or cricket query:\n"
                "   - Start with a bold heading: Match Title & Date.\n"
                "   - State the core verdict/winner in the first sentence.\n"
                "   - Provide Match Details: Venue, Toss, and Series Standing.\n"
                "   - Present a clean Markdown Table showing Team, Innings/Overs, and Top Performers.\n"
                "   - List bullet points for Player of the Match, top run scorers, top bowlers, and records/milestones.\n"
                "2. When web search data is provided below, synthesize all facts from it to give a definitive, detailed answer.\n"
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
