import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO
import tempfile
import fitz  # PyMuPDF for document processing

# App title and configuration
st.set_page_config(page_title="💬 Mavericks Bot")

# Sidebar: API key and model parameters
with st.sidebar:
    st.title('💬 Mavericks Chatbot')
    st.write("This chatbot uses Google's Gemini API for advanced language, image, voice, video, and document processing.")
    
    # API key input
    gemini_api_key = st.secrets.get('GEMINI_API_KEY') or st.text_input('Enter Gemini API key:', type='password')
    
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
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
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{mime_type.split('/')[-1]}") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name
    file = genai.upload_file(temp_file_path, mime_type=mime_type)
    os.unlink(temp_file_path)  # Clean up the temporary file
    return file

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

# Function to extract text from PDF
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Display or clear chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": ["How may I assist you today?"]}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["parts"][0])

def clear_chat_history():
    st.session_state.messages = [{"role": "model", "parts": ["How may I assist you today?"]}]
    st.session_state.files = []
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
        ]
    )
    
    chat = model.start_chat(history=[])
    
    # Add system instruction
    chat.send_message("You are Mavericks Bot, an advanced AI assistant created by Team Mavericks. You possess sophisticated image, video, audio, and document recognition capabilities, allowing you to analyze, understand, and provide insights on various types of content.")
    
    # Add chat history
    for message in st.session_state.messages:
        chat.send_message(message["parts"][0])
    
    # Add files to the conversation
    if files:
        wait_for_files_active(files)
        for file in files:
            chat.send_message(file)
    
    # Send the user's prompt
    response = chat.send_message(prompt_input)
    return response.text

# Main content: File Upload and Chat Input
if "files" not in st.session_state:
    st.session_state.files = []

prompt = st.chat_input()

if use_image:
    image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if image and "image" not in st.session_state:
        image_bytes = image.read()
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.session_state.messages.append({"role": "user", "parts": ["I've uploaded an image. Please analyze it."]})
        image_file = upload_to_gemini(image_bytes, "image/jpeg")
        st.session_state.files.append(image_file)
        st.session_state.image = True

if use_video:
    video = st.file_uploader("Upload a video", type=["mp4", "mov"])
    if video and "video" not in st.session_state:
        video_bytes = video.read()
        st.video(video)
        st.session_state.messages.append({"role": "user", "parts": ["I've uploaded a video. Please analyze it."]})
        video_file = upload_to_gemini(video_bytes, "video/mp4")
        st.session_state.files.append(video_file)
        st.session_state.video = True

if use_audio:
    audio = st.file_uploader("Upload an audio file", type=["ogg", "mp3", "wav"])
    if audio and "audio" not in st.session_state:
        audio_bytes = audio.read()
        st.audio(audio)
        st.session_state.messages.append({"role": "user", "parts": ["I've uploaded an audio file. Please analyze it."]})
        audio_file = upload_to_gemini(audio_bytes, "audio/ogg")
        st.session_state.files.append(audio_file)
        st.session_state.audio = True

if use_document:
    document = st.file_uploader("Upload a document", type=["pdf", "txt"])
    if document and "document" not in st.session_state:
        if document.type == "application/pdf":
            doc_text = extract_text_from_pdf(document)
        else:
            doc_text = document.getvalue().decode("utf-8")
        st.text_area("Document Content", doc_text, height=200)
        st.session_state.messages.append({"role": "user", "parts": ["I've uploaded a document. Please analyze its content."]})
        doc_file = upload_to_gemini(doc_text.encode(), "text/plain")
        st.session_state.files.append(doc_file)
        st.session_state.document = True

# Generate response when a prompt is entered or when media is uploaded
if prompt or (st.session_state.files and len(st.session_state.files) > len(st.session_state.messages) - 1):
    if prompt:
        st.session_state.messages.append({"role": "user", "parts": [prompt]})
        with st.chat_message("user"):
            st.write(prompt)

    # Generate response from Gemini
    with st.chat_message("model"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt or "Please analyze the uploaded content.", st.session_state.files)
            st.write(response)
            st.session_state.messages.append({"role": "model", "parts": [response]})

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["parts"][0])
