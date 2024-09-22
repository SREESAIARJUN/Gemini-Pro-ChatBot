import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO
import tempfile

# App title and configuration
st.set_page_config(page_title="💬 Mavericks Bot")

# Sidebar: API key and model parameters
with st.sidebar:
    st.title('💬 Mavericks Chatbot')
    st.write("This chatbot uses Google's Gemini API for advanced language, image, audio, video, and document processing.")
    
    # API key input
    gemini_api_key = st.secrets.get('GEMINI_API_KEY') or st.text_input('Enter Gemini API key:', type='password')
    
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        st.success('API key provided!', icon='✅')
    else:
        st.warning('Please enter valid Gemini API credentials!', icon='⚠')

    # Multimedia input options
    st.subheader('Input Types')
    use_image = st.checkbox("Upload Image")
    use_video = st.checkbox("Upload Video")
    use_audio = st.checkbox("Upload Audio")
    use_document = st.checkbox("Upload Document")

    # Adjustable model parameters
    st.subheader('Model Parameters')
    temperature = st.slider("Temperature", 0.0, 2.0, 1.0, step=0.1)
    top_p = st.slider("Top P", 0.0, 1.0, 0.95, step=0.05)
    top_k = st.slider("Top K", 1, 100, 64)
    max_output_tokens = st.slider("Max Output Tokens", 100, 8192, 8192)

# Model configuration
generation_config = {
    "temperature": temperature,
    "top_p": top_p,
    "top_k": top_k,
    "max_output_tokens": max_output_tokens,
}

# Function for uploading file using the File API
def upload_file_to_gemini(file_bytes, mime_type):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{mime_type.split('/')[-1]}") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name
    
    file = genai.upload_file(path=temp_file_path)
    os.unlink(temp_file_path)  # Clean up the temporary file
    return file

# Function to wait for files to be ready
def wait_for_file_active(file):
    while True:
        updated_file = genai.get_file(file.name)
        if updated_file.state.name == "ACTIVE":
            return updated_file
        elif updated_file.state.name == "FAILED":
            raise ValueError(f"File {file.name} failed to process")
        time.sleep(10)

# Display or clear chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "How may I assist you today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "model", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

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
        system_instruction = "You are Mavericks Bot, an advanced AI assistant created by Team Mavericks. You possess sophisticated image and video recognition capabilities, allowing you to analyze, understand, and provide insights on visual content. You also engage in voice-based interactions, providing real-time responses and conversational support. Additionally, you are equipped to analyze documents, extracting key information, summarizing content, and assisting with text-based queries and document-based tasks."
    )
    
    chat = model.start_chat(history=[
        {"role": msg["role"], "parts": [msg["content"]]}
        for msg in st.session_state.messages
    ])
    
    contents = []
    if files:
        contents.extend(files)
    contents.append(prompt_input)
    
    response = chat.send_message(contents)
    return response.text

# Main content: File Upload and Chat Input
files = []
prompt = st.chat_input()

if use_image:
    image = st.file_uploader("Upload an image", type=["png", "jpeg", "webp", "heic", "heif"])
    if image:
        image_bytes = image.read()
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.session_state.messages.append({"role": "model", "content": "Processing image..."})
        image_file = upload_file_to_gemini(image_bytes, image.type)
        files.append(wait_for_file_active(image_file))

if use_video:
    video = st.file_uploader("Upload a video", type=["mp4", "mpeg", "mov", "avi", "x-flv", "mpg", "webm", "wmv", "3gpp"])
    if video:
        video_bytes = video.read()
        st.video(video)
        st.session_state.messages.append({"role": "model", "content": "Processing video..."})
        video_file = upload_file_to_gemini(video_bytes, video.type)
        files.append(wait_for_file_active(video_file))

if use_audio:
    audio = st.file_uploader("Upload an audio file", type=["wav", "mp3", "aiff", "aac", "ogg", "flac"])
    if audio:
        audio_bytes = audio.read()
        st.audio(audio)
        st.session_state.messages.append({"role": "model", "content": "Processing audio..."})
        audio_file = upload_file_to_gemini(audio_bytes, audio.type)
        files.append(wait_for_file_active(audio_file))

if use_document:
    document = st.file_uploader("Upload a document", type=["txt", "pdf", "docx"])
    if document:
        document_bytes = document.read()
        st.session_state.messages.append({"role": "model", "content": f"Processing document: {document.name}"})
        document_file = upload_file_to_gemini(document_bytes, document.type)
        files.append(wait_for_file_active(document_file))

# Generate response when a prompt is entered
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate response from Gemini
    with st.chat_message("model"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt, files)
            st.write(response)
            st.session_state.messages.append({"role": "model", "content": response})
