import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO
import tempfile

# App title and configuration
st.set_page_config(page_title="💬 Mavericks Bot")

# API keys
with st.sidebar:
    st.title('💬 Mavericks Chatbot')
    st.write("This chatbot is built using Google's Gemini API for advanced language, image, voice, and video processing capabilities.")
    
    gemini_api_key = st.secrets.get('GEMINI_API_KEY') or st.text_input('Enter Gemini API key:', type='password')
    
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        st.success('API key provided!', icon='✅')
    else:
        st.warning('Please enter valid Gemini API credentials!', icon='⚠')

# Create the model
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
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ],
    system_instruction="You are Mavericks Bot, an advanced AI assistant created by Team Mavericks. You possess sophisticated image and video recognition capabilities, allowing you to analyze, understand, and provide insights on visual content. You also engage in voice-based interactions.",
)

# Function for uploading file to Gemini
def upload_to_gemini(file_bytes, mime_type):
    # Write the file to a temporary location first
    with tempfile.NamedTemporaryFile(delete=False, suffix=mime_type.split("/")[-1]) as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name
    file = genai.upload_file(temp_file_path, mime_type=mime_type)
    return file

# Function to wait for files to be ready
def wait_for_files_active(files):
    for file in files:
        while file.state.name == "PROCESSING":
            time.sleep(5)
            file = genai.get_file(file.name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")

# Display or clear chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating response from Gemini, including chat history
def generate_gemini_response(prompt_input, files=None):
    # Prepare chat history
    chat_history = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
    
    # Create a chat session with the chat history
    chat_session = model.start_chat(history=chat_history)

    if files:
        wait_for_files_active(files)
        for file in files:
            chat_session.send_message(file)

    # Send user input as a message and get the response
    response = chat_session.send_message(prompt_input)
    
    return response.text

# User inputs
image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
video = st.file_uploader("Upload a video", type=["mp4", "mov"])
audio = st.file_uploader("Upload an audio file", type=["ogg", "mp3", "wav"])
prompt = st.chat_input()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    files = []
    
    # Handle image upload
    if image:
        image_bytes = image.read()
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.session_state.messages.append({"role": "assistant", "content": "Processing image..."})
        image_file = upload_to_gemini(image_bytes, "image/jpeg")
        files.append(image_file)
    
    # Handle video upload
    if video:
        video_bytes = video.read()
        st.video(video)
        st.session_state.messages.append({"role": "assistant", "content": "Processing video..."})
        video_file = upload_to_gemini(video_bytes, "video/mp4")
        files.append(video_file)

    # Handle audio upload
    if audio:
        audio_bytes = audio.read()
        st.audio(audio)
        st.session_state.messages.append({"role": "assistant", "content": "Processing audio..."})
        audio_file = upload_to_gemini(audio_bytes, "audio/ogg")
        files.append(audio_file)

    # Generate response from Gemini
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt, files)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
