import streamlit as st
import os
import time
import google.generativeai as genai
from io import BytesIO
import tempfile

# Set up the page with a more stylized title and layout
st.set_page_config(page_title="💬 Mavericks Bot", layout="wide")

# Define custom colors and fonts for styling to give it a "WOW" look
USER_COLOR = "#262626"  # Darker tone for user's message
MODEL_COLOR = "#1c1c2b"  # Deep purple for model's message
USER_TEXT_COLOR = "#FFFFFF"  # White text for contrast
MODEL_TEXT_COLOR = "#00FFCC"  # Bright greenish-cyan for bot's text
FONT_FAMILY = "Comic Sans MS"  # Fun font style

# Sidebar: Ask for API key and allow file uploads
with st.sidebar:
    st.title('💬 Mavericks Chatbot')
    st.write("Using Google's Gemini API for advanced multimedia analysis.")
    
    # API key input
    gemini_api_key = st.secrets.get('GEMINI_API_KEY') or st.text_input('Enter Gemini API key:', type='password')
    
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        st.success('API key provided!', icon='✅')
    else:
        st.warning('Please enter valid Gemini API credentials!', icon='⚠')

    # Multimedia input options: Image or Video
    st.subheader('Input Types')
    use_image = st.checkbox("Upload Image")
    use_video = st.checkbox("Upload Video")

    # Customizable model parameters for tweaking the output
    st.subheader('Model Parameters')
    temperature = st.slider("Temperature", 0.0, 2.0, 1.0, step=0.1)
    top_p = st.slider("Top P", 0.0, 1.0, 0.95, step=0.05)
    top_k = st.slider("Top K", 1, 100, 64)
    max_output_tokens = st.slider("Max Output Tokens", 100, 8192, 8192)

# Model generation configuration
generation_config = {
    "temperature": temperature,
    "top_p": top_p,
    "top_k": top_k,
    "max_output_tokens": max_output_tokens,
}

# Function for uploading files to Gemini API
def upload_file_to_gemini(file_bytes, mime_type):
    """Uploads file to Google's Gemini API."""
    # Create a temporary file to handle the upload
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{mime_type.split('/')[-1]}") as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name

    # Use Google's API to upload the file and get a reference
    file = genai.upload_file(path=temp_file_path)
    os.unlink(temp_file_path)  # Clean up the temporary file
    return file

# Function to wait until the file is processed and active
def wait_for_file_active(file):
    """Polls the file status until it's ready for use in the API."""
    while True:
        updated_file = genai.get_file(file.name)
        if updated_file.state.name == "ACTIVE":
            return updated_file  # File is ready
        elif updated_file.state.name == "FAILED":
            raise ValueError(f"File {file.name} failed to process")  # Handle error case
        time.sleep(10)

# Initialize the chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "How may I assist you today?"}]

# Function to display a message in the chat interface with custom styling
def display_message(message):
    """Displays a message with alignment, color, and custom logo for user and bot."""
    if message["role"] == "user":
        st.markdown(
            f"""
            <div style='text-align: right; background-color: {USER_COLOR}; color: {USER_TEXT_COLOR}; 
                        font-family: {FONT_FAMILY}; padding: 10px; border-radius: 10px; margin: 5px;'>
                🧑‍💻 {message["content"]}
            </div>
            """, unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style='text-align: left; background-color: {MODEL_COLOR}; color: {MODEL_TEXT_COLOR}; 
                        font-family: {FONT_FAMILY}; padding: 10px; border-radius: 10px; margin: 5px;'>
                🤖 {message["content"]}
            </div>
            """, unsafe_allow_html=True
        )

# Display the chat history
for message in st.session_state.messages:
    display_message(message)

# Function to clear the chat history
def clear_chat_history():
    """Resets the chat to its initial state."""
    st.session_state.messages = [{"role": "model", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Generate a response using the Gemini API
def generate_gemini_response(prompt_input, files=None):
    """Generates a response from the Gemini API based on the chat history and input prompt."""
    # Initialize the Gemini model with custom parameters and safety settings
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=[  # Safety settings to avoid offensive content
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
        system_instruction="You are Mavericks Bot, an AI assistant with multimedia processing capabilities."
    )
    
    # Keep track of the conversation history
    chat = model.start_chat(history=[
        {"role": msg["role"], "parts": [msg["content"]]} for msg in st.session_state.messages
    ])
    
    contents = []
    if files:
        contents.extend(files)  # Append any uploaded files
    contents.append(prompt_input)  # Add the user prompt to the input

    # Send the message and get the response
    response = chat.send_message(contents)
    return response.text

# Main content: handle user input and file uploads
files = []
prompt = st.chat_input("Type your message here...")  # Chat input box

if use_image:
    # Image upload and display
    image = st.file_uploader("Upload an image", type=["png", "jpeg", "webp", "heic", "heif"])
    if image:
        image_bytes = image.read()
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.session_state.messages.append({"role": "model", "content": "Processing image..."})
        image_file = upload_file_to_gemini(image_bytes, image.type)
        files.append(wait_for_file_active(image_file))
        st.session_state["use_image"] = False

if use_video:
    # Video upload and display
    video = st.file_uploader("Upload a video", type=["mp4", "mpeg", "mov", "avi", "x-flv", "mpg", "webm", "wmv", "3gpp"])
    if video:
        video_bytes = video.read()
        st.video(video)
        st.session_state.messages.append({"role": "model", "content": "Processing video..."})
        video_file = upload_file_to_gemini(video_bytes, video.type)
        files.append(wait_for_file_active(video_file))
        st.session_state["use_video"] = False

# Generate response when the user enters a prompt
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    display_message({"role": "user", "content": prompt})

    # Generate response from Gemini API
    with st.spinner("Thinking..."):
        response = generate_gemini_response(prompt, files)
        st.session_state.messages.append({"role": "model", "content": response})
        display_message({"role": "model", "content": response})

# Reset the checkboxes after file uploads
if "use_image" in st.session_state and not st.session_state["use_image"]:
    st.session_state["use_image"] = False

if "use_video" in st.session_state and not st.session_state["use_video"]:
    st.session_state["use_video"] = False
