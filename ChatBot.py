import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO
import tempfile

# App title and configuration
st.set_page_config(page_title="💬 Mavericks Bot", layout="wide")

# Define style constants for professional tool
USER_COLOR = "#E8E8E8"  # Muted green for user message background
MODEL_COLOR = "#036165"  # Professional blue for model message background
USER_TEXT_COLOR = "#000000"  # White text for all messages for contrast
MODEL_TEXT_COLOR = "#FFFFFF"
BORDER_RADIUS = "8px"  # Rounded corners for chat bubbles
FONT_FAMILY = "Arial, sans-serif"  # Professional font family
USER_LOGO = "🧑‍💻"  # User's logo
MODEL_LOGO = "🤖"  # Model's logo

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

def display_message(message):
    """Display a message with custom alignment, color, and logos."""
    if message["role"] == "user":
        st.markdown(
            f"""
            <div style='display: flex; justify-content: flex-end;'>
                <div style='background-color: {USER_COLOR}; color: {USER_TEXT_COLOR}; padding: 10px; 
                border-radius: {BORDER_RADIUS}; margin: 5px; max-width: 70%; font-family: {FONT_FAMILY};'>
                    <span>{message["content"]}</span> <span>{USER_LOGO}</span>
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        if message.get("image"):
            # Display the uploaded image thumbnail next to the user's message
            st.markdown(
                f"""
                <div style='display: flex; justify-content: flex-end;'>
                    <img src="data:image/png;base64,{message['image']}" 
                    style='max-width: 150px; max-height: 150px; margin-left: 10px; border-radius: {BORDER_RADIUS};' />
                </div>
                """, unsafe_allow_html=True
            )
        elif message.get("video"):
            # Display the uploaded video thumbnail next to the user's message
            st.markdown(
                f"""
                <div style='display: flex; justify-content: flex-end;'>
                    <video controls style='max-width: 300px; max-height: 300px; margin-left: 10px; border-radius: {BORDER_RADIUS};'>
                        <source src="data:video/mp4;base64,{message['video']}" type="video/mp4" />
                    </video>
                </div>
                """, unsafe_allow_html=True
            )
    else:
        st.markdown(
            f"""
            <div style='display: flex; justify-content: flex-start;'>
                <div style='background-color: {MODEL_COLOR}; color: {MODEL_TEXT_COLOR}; padding: 10px; 
                border-radius: {BORDER_RADIUS}; margin: 5px; max-width: 70%; font-family: {FONT_FAMILY};'>
                    <span>{MODEL_LOGO}</span> <span>{message["content"]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

for message in st.session_state.messages:
    display_message(message)

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
        system_instruction="You are Mavericks Bot, an advanced AI assistant created by Team Mavericks. You possess sophisticated image and video recognition capabilities, allowing you to analyze, understand, and provide insights on visual content. You engage in real-time interactions by analyzing images and videos uploaded by users. Additionally, you support multimedia-based responses and generate insights or summaries based on visual content."
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
prompt = st.chat_input(placeholder="Type your message here...")

if use_image:
    image = st.file_uploader("Upload an image", type=["png", "jpeg", "webp", "heic", "heif"])
    if image:
        image_bytes = image.read()
        st.session_state.messages.append({"role": "user", "content": prompt, "image": image_bytes})
        st.image(image, caption="Uploaded Image", use_column_width=False, width=150)
        image_file = upload_file_to_gemini(image_bytes, image.type)
        files.append(wait_for_file_active(image_file))
        st.session_state["use_image"] = False  # Untick image checkbox after upload

if use_video:
    video = st.file_uploader("Upload a video", type=["mp4", "mpeg", "mov", "avi", "x-flv", "mpg", "webm", "wmv", "3gpp"])
    if video:
        video_bytes = video.read()
        st.session_state.messages.append({"role": "user", "content": prompt, "video": video_bytes})
        st.video(video)
        video_file = upload_file_to_gemini(video_bytes, video.type)
        files.append(wait_for_file_active(video_file))
        st.session_state["use_video"] = False  # Untick video checkbox after upload

# Generate response when a prompt is entered
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    display_message({"role": "user", "content": prompt})

    # Generate response from Gemini
    with st.spinner("Thinking... 🤔"):
        response = generate_gemini_response(prompt, files)
        st.session_state.messages.append({"role": "model", "content": response})
        display_message({"role": "model", "content": response})

# Ensure checkboxes are unticked after file upload
if "use_image" in st.session_state and not st.session_state["use_image"]:
    st.session_state["use_image"] = False

if "use_video" in st.session_state and not st.session_state["use_video"]:
    st.session_state["use_video"] = False
