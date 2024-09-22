import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO

# App title and configuration
st.set_page_config(page_title="💬 Mavericks Bot")

# Sidebar: API key and model parameters
with st.sidebar:
    st.title('💬 Mavericks Chatbot')
    st.write("This chatbot is built using Google's Gemini API for advanced language, image, voice, and video processing capabilities.")
    
    # API key input
    gemini_api_key = st.secrets.get('GEMINI_API_KEY') or st.text_input('Enter Gemini API key:', type='password')
    
    if gemini_api_key:
        try:
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            st.success('API key provided!', icon='✅')
        except Exception as e:
            st.error(f"Invalid API key: {str(e)}")
    else:
        st.warning('Please enter valid Gemini API credentials!', icon='⚠')

    # Multimedia input options
    st.subheader('Input Types')
    use_image = st.checkbox("Upload Image")
    use_video = st.checkbox("Upload Video")
    use_audio = st.checkbox("Upload Audio")
    use_document = st.checkbox("Upload Document")  # New document upload option

    # Adjustable model parameters
    st.subheader('Model Parameters')
    temperature = st.slider("Temperature", 0.1, 2.0, 1.0, step=0.1)
    top_p = st.slider("Top P", 0.1, 1.0, 0.95, step=0.05)
    top_k = st.slider("Top K", 1, 100, 64)
    max_output_tokens = st.slider("Max Output Tokens", 100, 8192, 8192)

# Model configuration
generation_config = {
    "temperature": temperature,
    "top_p": top_p,
    "top_k": top_k,
    "max_output_tokens": max_output_tokens,
}

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": ["How may I assist you today?"]}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["parts"][0])

def clear_chat_history():
    st.session_state.messages = [{"role": "model", "parts": ["How may I assist you today?"]}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to upload file using Gemini's File API
def upload_to_gemini(file_bytes, mime_type):
    try:
        # Upload the file using Gemini's File API
        uploaded_file = genai.upload_file(BytesIO(file_bytes), mime_type=mime_type)
        return uploaded_file
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None

# Function for generating response from Gemini, including chat history
def generate_gemini_response(prompt_input, files=None):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
        system_instruction="You are Mavericks Bot, an advanced AI assistant created by Team Mavericks. You possess sophisticated image and video recognition capabilities, allowing you to analyze, understand, and provide insights on visual content. You also engage in voice-based interactions.",
    )
    
    chat = model.start_chat(history=st.session_state.messages)
    
    if files:
        for file in files:
            chat.send_message(file)
    
    response = chat.send_message(prompt_input)
    return response.text

# Main content: File Upload and Chat Input
files = []
prompt = st.chat_input()

# Handle image input
if use_image:
    image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if image:
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.session_state.messages.append({"role": "model", "parts": ["Processing image..."]})
        # Directly upload file using Gemini's File API
        try:
            image_file = upload_to_gemini(image.read(), mime_type="image/jpeg")
            if image_file:
                files.append(image_file)
        except Exception as e:
            st.error(f"Error uploading image: {str(e)}")

# Handle video input
if use_video:
    video = st.file_uploader("Upload a video", type=["mp4", "mov"])
    if video:
        st.video(video)
        st.session_state.messages.append({"role": "model", "parts": ["Processing video..."]})
        try:
            video_file = upload_to_gemini(video.read(), mime_type="video/mp4")
            if video_file:
                files.append(video_file)
        except Exception as e:
            st.error(f"Error uploading video: {str(e)}")

# Handle audio input
if use_audio:
    audio = st.file_uploader("Upload an audio file", type=["ogg", "mp3", "wav"])
    if audio:
        st.audio(audio)
        st.session_state.messages.append({"role": "model", "parts": ["Processing audio..."]})
        try:
            audio_file = upload_to_gemini(audio.read(), mime_type="audio/ogg")
            if audio_file:
                files.append(audio_file)
        except Exception as e:
            st.error(f"Error uploading audio: {str(e)}")

# Handle document input
if use_document:
    document = st.file_uploader("Upload a document", type=["pdf", "txt"])
    if document:
        doc_extension = document.name.split(".")[-1]
        if doc_extension == "pdf":
            mime_type = "application/pdf"
        elif doc_extension == "txt":
            mime_type = "text/plain"
        st.session_state.messages.append({"role": "model", "parts": ["Processing document..."]})
        try:
            doc_file = upload_to_gemini(document.read(), mime_type=mime_type)
            if doc_file:
                files.append(doc_file)
        except Exception as e:
            st.error(f"Error uploading document: {str(e)}")

# Generate response when a prompt is entered
if prompt:
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate response from Gemini
    with st.chat_message("model"):
        with st.spinner("Thinking..."):
            try:
                response = generate_gemini_response(prompt, files)
                st.write(response)
                st.session_state.messages.append({"role": "model", "parts": [response]})
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
