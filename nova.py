import urllib.parse
import requests
import streamlit as st
from supabase import create_client
from streamlit_mic_recorder import speech_to_text

# Page Config
st.set_page_config(page_title="NOVA AI Generator", page_icon="🤖", layout="centered")

# Initialize Supabase client using Streamlit Secrets
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase = create_client(supabase_url, supabase_key)

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

    # 6-Digit OTP Input
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
# 2. LOGGED-IN CHAT, VOICE & IMAGE GENERATOR
# ---------------------------------------------------------
else:
    # Header & Logged-in info
    st.write(f"Logged in as: **{st.session_state.user.email}**")
    st.caption("Welcome! Ask anything or request an image (e.g., 'draw a futuristic city').")

    # Maintain conversation memory
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display prior conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"], caption="Generated Image 🎨")
            else:
                st.write(message["content"])

    # ---------------------------------------------------------
    # VOICE INPUT BUTTON
    # ---------------------------------------------------------
    st.write("🎙️ **Voice Assistant:** Click below to speak your prompt")
    spoken_text = speech_to_text(
        language='en',
        start_prompt="Click to Speak 🎙️",
        stop_prompt="Listening... (Click to Stop) 🛑",
        key='speech_input'
    )

    # Chat Text Input Box
    typed_prompt = st.chat_input("Ask NOVA AI or describe an image to generate...")

    # Determine active prompt (either spoken or typed)
    user_prompt = spoken_text if spoken_text else typed_prompt

    if user_prompt:
        # Display user input
        st.chat_message("user").write(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        # Simple detector for image requests
        image_keywords = ["image", "generate", "picture", "draw", "photo", "create an image", "logo"]
        is_image_request = any(word in user_prompt.lower() for word in image_keywords)

        if is_image_request:
            with st.chat_message("assistant"):
                st.write(f"🎨 Generating image for: *'{user_prompt}'*...")
                
                # Instant free image generation via Pollinations AI
                encoded_prompt = urllib.parse.quote(user_prompt)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"

                st.image(image_url, caption=f"Result for: {user_prompt}")
                st.session_state.messages.append({"role": "assistant", "content": image_url, "type": "image"})
        else:
            with st.chat_message("assistant"):
                # Free text response via Pollinations AI
                encoded_prompt = urllib.parse.quote(user_prompt)
                text_url = f"https://text.pollinations.ai/{encoded_prompt}"

                try:
                    response = requests.get(text_url).text
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception:
                    st.write("🤖 Sorry, I couldn't process that text request right now. Please try again.")
