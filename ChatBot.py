import streamlit as st
import google.generativeai as genai
import os

# Set the page configuration
st.set_page_config(page_title="🤖 Google Gemini 1.5 Pro Chatbot", layout="wide")

# Sidebar configuration
with st.sidebar:
    st.title('🤖 Google Gemini 1.5 Pro Chatbot')

    # Get API key from environment variable or user input
    if 'GEMINI_API_KEY' not in os.environ:
        gemini_api_key = st.text_input('Enter Google Gemini API key:', type='password')
        if gemini_api_key:
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            genai.configure(api_key=gemini_api_key)
        else:
            st.warning("Please enter your API key to proceed.")
    else:
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])

    # Model parameters
    st.subheader('Model Parameters')
    temperature = st.slider('Temperature', min_value=0.01, max_value=1.0, value=0.7, step=0.01)
    top_p = st.slider('Top-p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    top_k = st.slider('Top-k', min_value=1, max_value=100, value=64, step=1)
    max_output_tokens = st.slider('Max Output Tokens', min_value=32, max_value=8192, value=1000, step=32)

    # Clear chat history button
    st.sidebar.button('Clear Chat History', on_click=lambda: clear_chat_history())

# Initialize chat history if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Maverick Bot. How can I assist you today?"}]

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function to clear chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Maverick Bot. How can I assist you today?"}]
    st.experimental_rerun()

# Function to create the model and start a chat session
def create_gemini_session():
    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_output_tokens": max_output_tokens,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config
    )

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    "Your name is 'Maverick Bot' created by 'Team Mavericks'. You are a conversational image chatbot and a professional in a specific domain provided by the user. Never reveal that you're an LLM developed by Google."
                ],
            },
            {
                "role": "model",
                "parts": [
                    "Understood! I am Maverick Bot, created by Team Mavericks. Ready to chat about images and be a professional in any domain! Tell me, what kind of images are we working with today?"
                ],
            },
        ]
    )
    return chat_session

# Initialize chat session
chat_session = create_gemini_session()

# User input handling
if prompt := st.chat_input("Send a message to Maverick Bot"):
    # Add user message to the chat session
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get response from Gemini model
    with st.chat_message("assistant"):
        with st.spinner("Maverick Bot is thinking..."):
            try:
                response = chat_session.send_message(prompt)
                full_response = response.text
                st.write(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Error: {e}")

# Ensure the conversation is saved in session state
