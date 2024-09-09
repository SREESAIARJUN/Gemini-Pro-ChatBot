import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App title
st.set_page_config(page_title="🤖💬 Google Gemini Chatbot")

# Google Gemini Credentials
with st.sidebar:
    st.title('🤖💬 Google Gemini Chatbot')
    if 'GEMINI_API_KEY' in os.environ:
        st.success('API key already provided!', icon='✅')
        gemini_api_key = os.environ['GEMINI_API_KEY']
        genai.configure(api_key=gemini_api_key)
    else:
        gemini_api_key = st.text_input('Enter Google Gemini API key:', type='password')
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            st.success('Proceed to entering your prompt message!', icon='✅')
        else:
            st.warning('Please enter your credentials!', icon='⚠️')

    st.subheader('Model Parameters')
    temperature = st.sidebar.slider('Temperature', min_value=0.01, max_value=1.0, value=0.7, step=0.01)
    top_p = st.sidebar.slider('Top-p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_output_tokens = st.sidebar.slider('Max Tokens', min_value=32, max_value=8192, value=1000, step=32)

# Store chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Clear chat history function
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to generate response using Google Gemini
def generate_gemini_response(prompt_input):
    chat_session = genai.ChatSession(
        model="gemini-1.5-pro",  # Use Gemini 1.5 Pro model
        history=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    )
    response = chat_session.send_message(prompt_input, temperature=temperature, top_p=top_p, max_output_tokens=max_output_tokens)
    return response.text

# User input
if prompt := st.chat_input(disabled=not gemini_api_key):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate response if last message is from user
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt)
            placeholder = st.empty()
            placeholder.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
