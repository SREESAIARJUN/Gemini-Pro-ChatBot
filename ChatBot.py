import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO
import tempfile

# App title and configuration
st.set_page_config(page_title="💬 Mavericks Bot")

# --- Sidebar Settings ---
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

    # --- Multimedia Options ---
    st.subheader("Multimedia Options")
    use_image = st.checkbox("Enable Image Upload")
    use_video = st.checkbox("Enable Video Upload")
    use_audio = st.checkbox("Enable Audio Upload")

# --- Create the Model --- 
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-pro",
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

# --- Manage Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Clear chat history button
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# --- Generate Gemini Response with Chat History ---
def generate_gemini_response(prompt_input, files=None):
    # Construct the chat history 
    formatted_history = ""
    for i, msg in enumerate(st.session_state.messages):
        if i > 0:  
            formatted_history += f"{msg['role']}: {msg['content']}\n"

    # Combine chat history with the current prompt
    full_prompt = f"{formatted_history}user: {prompt_input}"

    # Generate response (using the 'files' parameter directly)
    response = model.generate_content(
        full_prompt,
        generation_config=generation_config,
        files=files  # Pass the files list here
    )
    return response.text

# --- Main Content Area ---
# --- User Inputs (Conditional based on sidebar) ---
image = None
video = None
audio = None

if use_image:
    image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
if use_video:
    video = st.file_uploader("Upload a video", type=["mp4", "mov"])
if use_audio:
    audio = st.file_uploader("Upload an audio file", type=["ogg", "mp3", "wav"])

prompt = st.chat_input()

# --- Process User Input and Generate Response ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    files = []

    if image:
        image_bytes = image.read()
        st.image(image, caption="Uploaded Image", use_column_width=True)
        image_file = upload_to_gemini(image_bytes, "image/jpeg")
        files.append(image_file)
    if video:
        video_bytes = video.read()
        st.video(video)
        video_file = upload_to_gemini(video_bytes, "video/mp4")
        files.append(video_file)
    if audio:
        audio_bytes = audio.read()
        st.audio(audio)
        audio_file = upload_to_gemini(audio_bytes, "audio/ogg")
        files.append(audio_file)

    if files:
        with st.spinner("Processing files..."):
            wait_for_files_active(files)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt, files)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
