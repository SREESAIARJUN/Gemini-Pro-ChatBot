import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO
import tempfile
import fitz  # PyMuPDF for document processing

# App title and configuration
st.set_page_config(page_title="💬 Mavericks Bot", layout="wide")

# Sidebar: API key and model parameters
with st.sidebar:
    st.title('💬 Mavericks Chatbot')
    st.write("This chatbot uses Google's Gemini API for advanced language, image, voice, video, and document processing.")
    
    # API key input
    if 'GEMINI_API_KEY' not in st.session_state:
        st.session_state.GEMINI_API_KEY = st.secrets.get('GEMINI_API_KEY', '')
    
    gemini_api_key = st.text_input('Enter Gemini API key:', value=st.session_state.GEMINI_API_KEY, type='password')
    
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        st.session_state.GEMINI_API_KEY = gemini_api_key
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        st.success('API key provided!', icon='✅')
    else:
        st.warning('Please enter valid Gemini API credentials!', icon='⚠')

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
    try:
        file = genai.upload_file(temp_file_path, mime_type=mime_type)
        return file
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None
    finally:
        os.unlink(temp_file_path)  # Clean up the temporary file

# Function to extract text from PDF
def extract_text_from_pdf(file):
    text = ""
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
    return text

# Display or clear chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": ["How may I assist you today?"]}]

if "files" not in st.session_state:
    st.session_state.files = []

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
        for file in files:
            chat.send_message(file)
    
    # Send the user's prompt
    try:
        response = chat.send_message(prompt_input)
        return response.text
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Main content: File Upload and Chat Input
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("File Upload")
    uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "mp4", "mov", "ogg", "mp3", "wav", "pdf", "txt"])
    
    if uploaded_file:
        file_type = uploaded_file.type.split('/')[0]
        if file_type == "image":
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        elif file_type == "video":
            st.video(uploaded_file)
        elif file_type == "audio":
            st.audio(uploaded_file)
        elif file_type == "application" and uploaded_file.type == "application/pdf":
            doc_text = extract_text_from_pdf(uploaded_file)
            st.text_area("Document Content", doc_text, height=200)
        elif uploaded_file.type == "text/plain":
            doc_text = uploaded_file.getvalue().decode("utf-8")
            st.text_area("Document Content", doc_text, height=200)
        
        if st.button("Process File"):
            with st.spinner("Processing file..."):
                if file_type in ["image", "video", "audio"]:
                    file = upload_to_gemini(uploaded_file.getvalue(), uploaded_file.type)
                else:
                    file = upload_to_gemini(doc_text.encode(), "text/plain")
                
                if file:
                    st.session_state.files.append(file)
                    st.session_state.messages.append({"role": "user", "parts": [f"I've uploaded a {file_type} file. Please analyze it."]})
                    st.experimental_rerun()

with col1:
    st.subheader("Chat")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["parts"][0])

    prompt = st.chat_input()

    if prompt:
        st.session_state.messages.append({"role": "user", "parts": [prompt]})
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response from Gemini
        with st.chat_message("model"):
            with st.spinner("Thinking..."):
                response = generate_gemini_response(prompt, st.session_state.files)
                st.write(response)
                st.session_state.messages.append({"role": "model", "parts": [response]})
