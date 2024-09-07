import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Google Gemini API key
with st.sidebar:
    st.title('🤖💬 Google Gemini Chatbot')
    API_KEY = os.getenv("GEMINI_API_KEY")  # Load API key from environment or .env
    if API_KEY:
        st.success('API key loaded from environment!', icon='✅')
        genai.configure(api_key=API_KEY)
    else:
        API_KEY = st.text_input('Enter Google Gemini API Key:', type='password')
        if API_KEY:
            genai.configure(api_key=API_KEY)
            st.success('API key set!', icon='✅')
        else:
            st.warning('Please enter a valid API key to proceed.', icon='⚠️')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input prompt
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate a response using Google Gemini API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Start chat session with Gemini
        chat_session = genai.ChatSession(
            history=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        )
        response = chat_session.send_message(prompt)

        # Display the response in real-time (simulating streaming behavior)
        full_response = response.text
        message_placeholder.markdown(full_response)

    # Save assistant's response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
