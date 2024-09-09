import streamlit as st
import os
import google.generativeai as genai

# App title
st.set_page_config(page_title="🦙💬 Maverick Bot Chatbot")

# Google Generative AI Credentials (replace with your API key)
os.environ["GEMINI_API_KEY"] = 'AIzaSyBHFH2xfKgxvIxEJL7EVyXIg64a3JmKQkI'

# Configure Google Generative AI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Chatbot configuration
selected_model = "Gemini-1.5-pro"
generation_config = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 512,
    "response_mime_type": "text/plain",
}

# Chat history
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "model", "content": "How may I assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function to generate response using Gemini AI
def generate_gemini_response(prompt):
    try:
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
                    ]
                },
                {
                    "role": "model",
                    "parts": [
                        "Understood! I am Maverick Bot, developed by Team Mavericks. Tell me, what kind of images are we working with today, and what role would you like me to play?"
                    ]
                }
            ]
        )
        response = chat_session.send_message(prompt)
        return response.text
    except Exception as e:
        # Handle exceptions gracefully, e.g., log error, retry, provide user-friendly message
        st.error(f"An error occurred: {e}")
        return "I couldn't process your request. Please try again later."

# User-provided prompt
if prompt := st.chat_input():
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
