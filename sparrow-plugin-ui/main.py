import streamlit as st
from tools.utilities import load_css
from pathlib import Path
import base64
import requests
from config import settings
from io import BytesIO
import os
import mimetypes


__version__ = "1.0.0"
app_name = "Receipt Assistant"

st.set_page_config(
    page_title=app_name,
    page_icon="favicon.ico",
    layout="centered"
)
ss = st.session_state

load_css()


def ui_spacer(n=2, line=False, next_n=0):
    for _ in range(n):
        st.write('')
    if line:
        st.tabs([' '])
    for _ in range(next_n):
        st.write('')


def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded


def ui_info():
    st.sidebar.markdown(
        '''[<img src='data:image/png;base64,{}' class='img-fluid' width=75 height=75>](https://streamlit.io/)'''.format(
            img_to_bytes("sparrow_logo.png")), unsafe_allow_html=True)

    st.markdown(f"""
        # Receipt Assistant
        version {__version__}
    
        Manage receipts with Sparrow. You can read, store and review your receipts.
    """)

    ui_spacer(1)
    st.write("Made by [Katana ML](https://www.katanaml.io).", unsafe_allow_html=True)
    ui_spacer(1)
    st.markdown("""
        You can use this app to upload your receipt for usage in ChatGPT. After uploading, you will receive a key to 
        copy/paste into ChatGPT. ChatGPT will fetch the data using that key to answer your questions about the receipt. 
        File data will be removed automatically from this app after reading it by ChatGPT or after 15 minutes, 
        whichever comes first.
    """)

    ui_spacer(1)

    st.markdown("""
        Thank you for your interest in Receipt Assistant.
        If you like this app you can ❤️ [follow us](https://twitter.com/katana_ml)
        on Twitter for news and updates.
    """)

    ui_spacer(1)

    st.markdown('Source code can be found [here](https://github.com/katanaml/sparrow).')


def ui_file_upload():
    st.write('## Upload your receipt file')

    with st.form("upload-form", clear_on_submit=True):
        uploaded_file = st.file_uploader("Upload file", accept_multiple_files=False,
                                         type=['png', 'jpg', 'jpeg', 'pdf'],
                                         help="When file will be processed, you will receive a key for ChatGPT",
                                         label_visibility="collapsed")
        submitted = st.form_submit_button("Upload")

        if submitted and uploaded_file is not None:
            success_key = file_upload(uploaded_file)
            st.success(f"Success! Copy this key into ChatGPT: {success_key}", icon="✅")


def ui_sample_receipts():
    sample_receipts = {
        "Receipt 1": "sample_receipts/inout-20211211_001.jpg",
        "Receipt 2": "sample_receipts/ross-20211211_010.jpg",
        "Receipt 3": "sample_receipts/wholefoods-20211211_005.jpg"
    }

    # Display images side by side
    col1, col2, col3 = st.columns(3)
    selected_receipt = None

    with col1:
        col1_left, col1_button, col1_right = st.columns([1, 2, 1])
        with col1_button:
            if st.button("Upload", key="upload1"):
                selected_receipt = "Receipt 1"
        img = st.image(sample_receipts["Receipt 1"], width=200)
    with col2:
        col2_left, col2_button, col2_right = st.columns([1, 2, 1])
        with col2_button:
            if st.button("Upload", key="upload2"):
                selected_receipt = "Receipt 2"
        img = st.image(sample_receipts["Receipt 2"], width=200)
    with col3:
        col3_left, col3_button, col3_right = st.columns([1, 2, 1])
        with col3_button:
            if st.button("Upload", key="upload3"):
                selected_receipt = "Receipt 3"
        img = st.image(sample_receipts["Receipt 3"], width=200)

    if selected_receipt is not None:
        file_path = sample_receipts[selected_receipt]
        with open(sample_receipts[selected_receipt], "rb") as f:
            bytes_data = f.read()
            buffer = BytesIO(bytes_data)
            buffer.name = os.path.basename(file_path)  # Add the 'name' attribute
            buffer.type = mimetypes.guess_type(file_path)[0]  # Add the 'type' attribute

            success_key = file_upload(buffer)
            st.success(f"Success! Copy this key into ChatGPT: {success_key}", icon="✅")


def file_upload(uploaded_file):
    api_url = settings.api_data_url

    # Prepare the payload
    files = {
        'file': (uploaded_file.name, uploaded_file, uploaded_file.type)
    }

    data = {
        'image_url': '',
        'post_processing': 'true',
        'sparrow_key': settings.sparrow_key
    }

    with st.spinner("Processing file..."):
        response = requests.post(api_url, data=data, files=files, timeout=180)

    if response.status_code != 200:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)

        return "Error, contact support"

    success_key = response.json()
    return success_key


with st.sidebar:
    ui_info()

ui_file_upload()

st.divider()
st.write('## Sample receipts')
ui_sample_receipts()

