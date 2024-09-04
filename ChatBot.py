# Author - Arjun Sai

import streamlit as st
import google.generativeai as genai
import google.ai.generativelanguage as glm
from dotenv import load_dotenv
from PIL import Image
import os
import io

# Load environment variables
load_dotenv()

# Convert image to byte array
def image_to_byte_array(image: Image) -> bytes:
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=image.format)
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr

# Configure the API
API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Unified model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

# Styling for chat interface
def apply_custom_css():
    st.markdown("""
        <style>
            .user-message {
                background-color: #f0f0f5;
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 10px;
                max-width: 80%;
                text-align: left;
                color: black;
                font-family: "Arial", sans-serif;
            }
            .bot-message {
                background-color: #007BFF;
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 10px;
                max-width: 80%;
                text-align: left;
                color: white;
                font-family: "Arial", sans-serif;
            }
            .message-container {
                display: flex;
                flex-direction: column;
                align-items: flex-start;
            }
            .user-container {
                align-items: flex-end;
            }
            .image-container img {
                border-radius: 10px;
                margin-top: 10px;
                max-width: 40%;
            }
            .input-container {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                padding: 10px;
                background-color: white;
            }
        </style>
    """, unsafe_allow_html=True)

# Main function
def main():
    apply_custom_css()

    st.title("Maverick Bot")

    # Display chat conversation in real-time
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f'<div class="message-container user-container"><div class="user-message">{chat["content"]}</div></div>', unsafe_allow_html=True)
            if chat.get("image"):
                st.image(Image.open(chat["image"]), caption="You uploaded", use_column_width=True)
        else:
            st.markdown(f'<div class="message-container"><div class="bot-message">{chat["content"]}</div></div>', unsafe_allow_html=True)

    # Input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    with st.form(key='input_form'):
        user_prompt = st.text_input("Type your message here...", placeholder="Type your message here")
        uploaded_image = st.file_uploader("Upload an image (optional)", accept_multiple_files=False, type=["png", "jpg", "jpeg", "img", "webp"])
        submit_button = st.form_submit_button(label='SEND')

    # Handle form submission
    if submit_button and (user_prompt or uploaded_image):
        # Add user input to the chat history
        st.session_state.chat_history.append({"role": "user", "content": user_prompt, "image": uploaded_image})

        # Prepare parts for the model
        parts = [glm.Part(text=user_prompt)]
        if uploaded_image:
            image = Image.open(uploaded_image)
            parts.append(
                glm.Part(
                    inline_data=glm.Blob(
                        mime_type="image/jpeg",
                        data=image_to_byte_array(image)
                    )
                )
            )

        # Generate the bot's response
        response = model.generate_content(glm.Content(parts=parts))
        st.session_state.chat_history.append({"role": "assistant", "content": response.text})

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
