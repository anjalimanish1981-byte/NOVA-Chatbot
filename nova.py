import urllib.parse
import streamlit as st
from supabase import create_client
from streamlit_mic_recorder import speech_to_text
from tavily import TavilyClient
from groq import Groq

# Page Config
st.set_page_config(page_title="NOVA AI Generator", page_icon="🤖", layout="centered")

# Hardcoded Keys
SUPABASE_URL = "https://wecsfbazfodlypiybymb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndlY3NmYmF6Zm9kbHlwaXlieW1iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ4MTYyOTksImV4cCI6MjEwMDM5MjI5OX0.dHkQR-3EDtIBRzhv0FT7cXBXv26ZG3IfV7ip2GjFcYk"
TAVILY_API_KEY = "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"
GROQ_API_KEY = "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"

# Initialize Clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

st.title("🤖 NOVA AI Generator")

# Helper functions for database chat history
def load_chat_history(user_id):
    try:
        res = supabase.table("chat_history").select("*").eq("user_id", user_id).order("id", desc=False).execute()
        return res.data if res.data else []
    except Exception as e:
        return []

def save_chat_message(user_id, role, content, msg_type="text"):
    try:
        supabase.table("chat_history").insert({
            "user_id": str(user_id),
            "role": role,
            "content": content,
            "type": msg_type
        }).execute()
    except Exception as e:
        pass

# ---------------------------------------------------------
# 1. USER AUTHENTICATION SECTION (OTP SIGN IN)
# ---------------------------------------------------------
if "user" not in st.session_state:
    st.subheader("Sign In to Access NOVA AI")
    email = st.text_input("Enter your email address:")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Send OTP Code 📩", use_container_width=True):
            if email:
                try:
                    res = supabase.auth.sign_in_with_otp({"email": email})
                    st.success("Verification code sent to your email! Check your inbox.")
                except Exception as e:
                    st.error(f"Error sending code: {e}")
            else:
                st.warning("Please enter a valid email address.")

    otp_code = st.text_input("Enter the 6-digit code received in email:", type="password")

    if st.button("Verify & Sign In 🚀", use_container_width=True):
        if email and otp_code:
            try:
                res = supabase.auth.verify_otp({"email": email, "token": otp_code, "type": "email"})
                st.session_state.user = res.user
                st.success("Successfully signed in!")
                st.rerun()
            except Exception as e:
                st.error("Invalid or expired code. Please try again.")

# ---------------------------------------------------------
# 2. LOGGED-IN CHAT, VOICE, IMAGE & GROQ/TAVILY AI
# ---------------------------------------------------------
else:
    user_email = st.session_state.user.email
    # Extract name from email (e.g., anjalimanish1981@gmail.com -> Anjalimanish1981)
    user_name = user_email.split("@")[0].capitalize() if "@" in user_email else "User"

    # Display personal greeting banner
    st.write(f"### 👋 Welcome back, **{user_name}**!")
    st.caption(f"Logged in as: `{user_email}`")
    
    col_out, _ = st.columns([1, 3])
    with col_out:
        if st.button("Sign Out 🚪"):
            supabase.auth.sign_out()
            st.session_state.clear()
            st.rerun()

    st.divider()

    # Load persistent history from Supabase on initial login
    if "messages" not in st.session_state:
        db_history = load_chat_history(st.session_state.user.id)
        if db_history:
            st.session_state.messages = db_history
        else:
            # First welcome message from NOVA if history is completely empty
            welcome_msg = f"Hello {user_name}! 👋 I am NOVA AI, your personal assistant. How can I help you today?"
            st.session_state.messages = [{"role": "assistant", "content": welcome_msg, "type": "text"}]
            save_chat_message(st.session_state.user.id, "assistant", welcome_msg, "text")

    # Display all saved conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"], caption="Generated Image 🎨")
            else:
                st.write(message["content"])

    # Voice Input
    st.write("🎙️ **Voice Assistant:** Click below to speak your prompt")
    spoken_text = speech_to_text(
        language='en',
        start_prompt="Click to Speak 🎙️",
        stop_prompt="Listening... (Click to Stop) 🛑",
        key='speech_input'
    )

    typed_prompt = st.chat_input(f"Ask NOVA AI anything, {user_name}...")
    user_prompt = spoken_text if spoken_text else typed_prompt

    if user_prompt:
        st.chat_message("user").write(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt, "type": "text"})
        save_chat_message(st.session_state.user.id, "user", user_prompt, "text")

        # Image generation keywords check
        image_keywords = ["image", "generate", "picture", "draw", "photo", "create an image", "logo"]
        is_image_request = any(word in user_prompt.lower() for word in image_keywords)

        if is_image_request:
            with st.chat_message("assistant"):
                st.write(f"🎨 Generating image for: *'{user_prompt}'*...")
                encoded_prompt = urllib.parse.quote(user_prompt)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"

                st.image(image_url, caption=f"Result for: {user_prompt}")
                st.session_state.messages.append({"role": "assistant", "content": image_url, "type": "image"})
                save_chat_message(st.session_state.user.id, "assistant", image_url, "image")
        else:
            with st.chat_message("assistant"):
                bot_response = ""

                # Check if prompt requires a web search
                search_keywords = ["latest", "news", "today", "search", "who is", "weather", "score", "rate"]
                needs_search = any(word in user_prompt.lower() for word in search_keywords)

                # 1. Search with Tavily if search keywords detected
                if needs_search and tavily_client:
                    try:
                        search_res = tavily_client.search(query=user_prompt, max_results=3)
                        results = search_res.get("results", [])
                        if results:
                            bot_response = "🌐 **Live Web Search Results:**\n\n"
                            for r in results:
                                bot_response += f"• **[{r['title']}]({r['url']})**\n{r['content']}\n\n"
                    except Exception:
                        bot_response = ""

                # 2. Process query with Groq LLM (LLaMA 3.3)
                if not bot_response and groq_client:
                    try:
                        chat_completion = groq_client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system", 
                                    "content": f"You are NOVA AI, a helpful and friendly personal assistant. You are talking to {user_name}."
                                },
                                {"role": "user", "content": user_prompt}
                            ],
                            model="llama-3.3-70b-versatile",
                        )
                        bot_response = chat_completion.choices[0].message.content
                    except Exception as e:
                        bot_response = f"🤖 Hello {user_name}! How can I assist you with: '{user_prompt}'?"

                if not bot_response:
                    bot_response = f"🤖 Hello {user_name}! How can I help you today?"

                st.write(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response, "type": "text"})
                save_chat_message(st.session_state.user.id, "assistant", bot_response, "text")
