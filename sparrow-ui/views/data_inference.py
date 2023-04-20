import streamlit as st
import os
import time


class DataInference:
    class Model:
        # pageTitle = "Data Inference"
        subheader_2 = "Upload"

        upload_help = "Upload a file to extract data from it"
        upload_button_text = "Upload"
        upload_button_text_desc = "Choose a file"

    def view(self, model):
        # st.title(model.pageTitle)

        with st.sidebar:
            st.markdown("---")
            st.subheader(model.subheader_2)

            with st.form("upload-form", clear_on_submit=True):
                uploaded_file = st.file_uploader(model.upload_button_text_desc, accept_multiple_files=False,
                                                 type=['png', 'jpg', 'jpeg'],
                                                 help=model.upload_help)
                submitted = st.form_submit_button(model.upload_button_text)

                if submitted and uploaded_file is not None:
                    ret = self.upload_file(uploaded_file)

                    if ret is not False:
                        pass

    def upload_file(self, uploaded_file):
        if uploaded_file is not None:
            timestamp = str(time.time())
            timestamp = timestamp.replace(".", "")

            file_name, file_extension = os.path.splitext(uploaded_file.name)
            uploaded_file.name = file_name + "_" + timestamp + file_extension

            if os.path.exists(os.path.join("docs/inference/", uploaded_file.name)):
                st.write("File already exists")
                return False

            if len(uploaded_file.name) > 500:
                st.write("File name too long")
                return False

            with open(os.path.join("docs/inference/", uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success("File uploaded successfully")