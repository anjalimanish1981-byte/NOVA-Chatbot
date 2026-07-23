import streamlit as st
from supabase import create_client

# Initialize Supabase client
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase = create_client(supabase_url, supabase_key)

st.title("🤖 NOVA AI Generator")

# Check if user is logged in
if "user" not in st.session_state:
    st.subheader("Sign In")
    email = st.text_input("Enter your email address:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send OTP Code 📩"):
            if email:
                res = supabase.auth.sign_in_with_otp({"email": email})
                st.success("Verification code sent to your email!")
            else:
                st.warning("Please enter a valid email.")

    # --- THIS IS THE 6-DIGIT CODE INPUT BOX ---
    otp_code = st.text_input("Enter the 6-digit code received in email:", type="password")
    
    if st.button("Verify & Sign In 🚀"):
        if email and otp_code:
            try:
                res = supabase.auth.verify_otp({"email": email, "token": otp_code, "type": "email"})
                st.session_state.user = res.user
                st.success("Successfully signed in!")
                st.rerun()
            except Exception as e:
                st.error("Invalid or expired code. Please try again.")

else:
    st.write(f"Logged in as: {st.session_state.user.email}")
    st.write("Welcome! Type your prompt below to create text or images.")
