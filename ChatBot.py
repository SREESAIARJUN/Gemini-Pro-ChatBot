# Author - Arjun Sai

import streamlit as st 
import google.generativeai as genai 
import google.ai.generativelanguage as glm 
from dotenv import load_dotenv
from PIL import Image
import os 
import io 

load_dotenv()

def image_to_byte_array(image: Image) -> bytes:
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=image.format)
    imgByteArr=imgByteArr.getvalue()
    return imgByteArr

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

def main():
    st.header("Maverick Bot - Conversational Image and Text Chat")

    # Display chat conversation in real-time
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"**You:** {chat['content']}")
            if chat.get("image"):
                st.image(Image.open(chat["image"]), caption="You uploaded", use_column_width=True)
        else:
            st.markdown(f"**Maverick Bot:** {chat['content']}")

    user_prompt = st.text_input("Enter your message or prompt...", placeholder="Type your message here", label_visibility="visible")
    uploaded_image = st.file_uploader("Upload an image (optional)", accept_multiple_files=False, type=["png", "jpg", "jpeg", "img", "webp"])

    if st.button("SEND", use_container_width=True):
        if user_prompt or uploaded_image:
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

            # Rerun to display the updated conversation
            st.experimental_rerun()

if __name__ == "__main__":
    main()
