import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

def page_setup():
    st.header("Chat with different types of media/files!")

    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

def get_typeofpdf():
    st.sidebar.header("Select type of Media")
    typepdf = st.sidebar.radio("Choose one:",
                               ("PDF files",
                                "Images",
                                "Video, mp4 file",
                                "Audio files"))
    return typepdf

def get_llminfo():
    st.sidebar.header("Options")
    model = st.sidebar.radio("Choose LLM:",
                             ("gemini-1.5-flash", "gemini-1.5-pro"))
    temperature = st.sidebar.slider("Temperature:", 0.0, 2.0, 1.0, 0.25)
    top_p = st.sidebar.slider("Top P:", 0.0, 1.0, 0.94, 0.01)
    max_tokens = st.sidebar.slider("Maximum Tokens:", 100, 5000, 2000, 100)
    return model, temperature, top_p, max_tokens

# Initialize session state to store chat history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

def main():
    page_setup()
    typepdf = get_typeofpdf()
    model, temperature, top_p, max_tokens = get_llminfo()

    if typepdf == "PDF files":
        uploaded_files = st.file_uploader("Choose 1 or more PDF", type='pdf', accept_multiple_files=True)

        if uploaded_files:
            text = ""
            for pdf in uploaded_files:
                pdf_reader = PdfReader(pdf)
                for page in pdf_reader.pages:
                    text += page.extract_text()

            # Display previous chat history
            for message in st.session_state['chat_history']:
                st.write(f"**You:** {message['question']}")
                st.write(f"**Assistant:** {message['response']}")

            question = st.text_input("Ask a question related to the PDF")
            if question:
                # Generate response using the LLM
                generation_config = {
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_output_tokens": max_tokens,
                    "response_mime_type": "text/plain",
                }
                model_instance = genai.GenerativeModel(
                    model_name=model,
                    generation_config=generation_config,
                )
                response = model_instance.generate_content([question, text])

                # Store the question and response in session state
                st.session_state['chat_history'].append({
                    "question": question,
                    "response": response.text
                })

                # Display the new interaction
                st.write(f"**You:** {question}")
                st.write(f"**Assistant:** {response.text}")

    # Implement similar logic for Images, Videos, and Audio types.
    # Each can maintain its respective interaction and use case.
    # The session state will store history across different media types.

if __name__ == '__main__':
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    main()
