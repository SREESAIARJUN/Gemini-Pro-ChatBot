import streamlit as st
import os
import google.generativeai as genai

# App title
st.set_page_config(page_title="🦙💬 Maverick Bot Chatbot")

# Google Generative AI Credentials
with st.sidebar:
    st.title('🦙💬 Maverick Bot Chatbot')
    if 'GEMINI_API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        gemini_api = st.secrets['GEMINI_API_KEY']
    else:
        gemini_api = st.text_input('Enter Google Gemini API token:', type='password')
        if not gemini_api:
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    os.environ['GEMINI_API_KEY'] = gemini_api

    st.subheader('Models and parameters')
    selected_model = st.sidebar.selectbox('Choose a model', ['Gemini-1.5-pro'], key='selected_model')
    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=2.0, value=1.0, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.95, step=0.01)
    max_output_tokens = st.sidebar.slider('max_output_tokens', min_value=32, max_value=8192, value=512, step=32)
    top_k = st.sidebar.slider('top_k', min_value=1, max_value=128, value=64, step=1)

# Configure Google Generative AI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
    "temperature": temperature,
    "top_p": top_p,
    "top_k": top_k,
    "max_output_tokens": max_output_tokens,
    "response_mime_type": "text/plain",
}

# Store chatbot responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "model", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "model", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to generate response using Gemini AI
def generate_gemini_response(prompt_input):
    model = genai.GenerativeModel(
        model_name=selected_model,
        generation_config=generation_config
    )
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    "Your name is 'Maverick Bot' created by 'Team Mavericks'. You're a conversational image chatbot. You're also a professional in the specific domain provided by the user."
                ],
            },
            {
                "role": "model",
                "parts": [
                    "Understood! I am Maverick Bot, developed by Team Mavericks. Tell me, what kind of images are we working with today, and what role would you like me to play?"
                ],
            },
        ]
    )
    response = chat_session.send_message(prompt_input)
    return response.text

# User-provided prompt
if prompt := st.chat_input(disabled=not gemini_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if the last message is not from the model
if st.session_state.messages[-1]["role"] != "model":
    with st.chat_message("model"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt)
            placeholder = st.empty()
            placeholder.markdown(response)
    message = {"role": "model", "content": response}
    st.session_state.messages.append(message)
