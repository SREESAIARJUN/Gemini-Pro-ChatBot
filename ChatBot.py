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

# Function for uploading file to Gemini
def upload_to_gemini(file_bytes, mime_type):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{mime_type.split('/')[-1]}") as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        file = genai.upload_file(temp_file_path, mime_type=mime_type)
        os.unlink(temp_file_path)  # Clean up the temporary file
        return file
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None

# Function to wait for files to be ready
def wait_for_files_active(files):
    for file in files:
        while True:
            try:
                updated_file = genai.get_file(file.name)
                if updated_file.state == "ACTIVE":
                    break
                elif updated_file.state == "FAILED":
                    raise Exception(f"File {file.name} failed to process")
                time.sleep(1)
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                break

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
        wait_for_files_active(files)
        for file in files:
            chat.send_message(file)
    
    response = chat.send_message(prompt_input)
    return response.text

# Main content: File Upload and Chat Input
files = []
prompt = st.chat_input()

if use_image:
    image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if image:
        image_bytes = image.read()
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.session_state.messages.append({"role": "model", "parts": ["Processing image..."]})
        image_file = upload_to_gemini(image_bytes, "image/jpeg")
        if image_file:
            files.append(image_file)

if use_video:
    video = st.file_uploader("Upload a video", type=["mp4", "mov"])
    if video:
        video_bytes = video.read()
        st.video(video)
        st.session_state.messages.append({"role": "model", "parts": ["Processing video..."]})
        video_file = upload_to_gemini(video_bytes, "video/mp4")
        if video_file:
            files.append(video_file)

if use_audio:
    audio = st.file_uploader("Upload an audio file", type=["ogg", "mp3", "wav"])
    if audio:
        audio_bytes = audio.read()
        st.audio(audio)
        st.session_state.messages.append({"role": "model", "parts": ["Processing audio..."]})
        audio_file = upload_to_gemini(audio_bytes, "audio/ogg")
        if audio_file:
            files.append(audio_file)

# Document upload and processing
if use_document:
    document = st.file_uploader("Upload a document", type=["pdf", "txt"])
    if document:
        document_bytes = document.read()
        doc_extension = document.name.split(".")[-1]
        if doc_extension == "pdf":
            mime_type = "application/pdf"
        elif doc_extension == "txt":
            mime_type = "text/plain"
        st.session_state.messages.append({"role": "model", "parts": ["Processing document..."]})
        doc_file = upload_to_gemini(document_bytes, mime_type)
        if doc_file:
            files.append(doc_file)

# Generate response when a prompt is entered
if prompt:
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate response from Gemini
    with st.chat_message("model"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt, files)
            st.write(response)
            st.session_state.messages.append({"role": "model", "parts": [response]})
