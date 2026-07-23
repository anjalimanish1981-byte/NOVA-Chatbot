import urllib.parse
import streamlit as st
from supabase import create_client
from streamlit_mic_recorder import speech_to_text
from tavily import TavilyClient
from groq import Groq

# Page Config
st.set_page_config(page_title="NOVA AI Generator", page_icon="🤖", layout="centered")

# Hardcoded Keys (Bypassing Streamlit Secrets Box)
SUPABASE_URL = "https://wecsfbazfodlypiybymb.supabase.co"
SUPABASE_KEY = "sb_publishable_gVeF5AWQnSWRQJuWMzBLWiAju"
TAVILY_API_KEY = "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"
GROQ_API_KEY = "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"

# Initialize Clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

st.title("🤖 NOVA AI Generator")

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
    st.write(f"Logged in as: **{st.session_state.user.email}**")
    st.caption("Welcome! Ask anything, request an image, or search the web.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display prior conversation history
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

    typed_prompt = st.chat_input("Ask NOVA AI or describe an image to generate...")
    user_prompt = spoken_text if spoken_text else typed_prompt

    if user_prompt:
        st.chat_message("user").write(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

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
                                {"role": "system", "content": "You are NOVA AI, a smart and friendly personal assistant."},
                                {"role": "user", "content": user_prompt}
                            ],
                            model="llama-3.3-70b-versatile",
                        )
                        bot_response = chat_completion.choices[0].message.content
                    except Exception as e:
                        bot_response = f"🤖 I am NOVA AI! How can I assist you with: '{user_prompt}'?"

                if not bot_response:
                    bot_response = f"🤖 Hello! I am NOVA AI. How can I help you today?"

                st.write(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
