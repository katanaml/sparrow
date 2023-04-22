import streamlit as st
import os
import time
from PIL import Image
import math
from streamlit_sparrow_labeling import st_sparrow_labeling
import requests
from config import settings


class DataInference:
    class Model:
        # pageTitle = "Data Inference"
        subheader_2 = "Upload"
        initial_msg = "Please upload a file for inference"

        upload_help = "Upload a file to extract data from it"
        upload_button_text = "Upload"
        upload_button_text_desc = "Choose a file"

        extract_data = "Extract Data"

        model_in_use = "donut"

        img_file = None

        def set_image_file(self, img_file):
            st.session_state['img_file'] = img_file

        def get_image_file(self):
            if 'img_file' not in st.session_state:
                return None
            return st.session_state['img_file']

        data_result = None

        def set_data_result(self, data_result):
            st.session_state['data_result'] = data_result

        def get_data_result(self):
            if 'data_result' not in st.session_state:
                return None
            return st.session_state['data_result']

    def view(self, model, ui_width, device_type, device_width):
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
                        model.set_image_file(ret)
                        model.set_data_result(None)

        if model.get_image_file() is not None:
            doc_img = Image.open(model.get_image_file())
            doc_height = doc_img.height
            doc_width = doc_img.width

            canvas_width, number_of_columns = self.canvas_available_width(ui_width, doc_width, device_type,
                                                                          device_width)

            if number_of_columns > 1:
                col1, col2 = st.columns([number_of_columns, 10 - number_of_columns])
                with col1:
                    self.render_doc(model, doc_img, canvas_width, doc_height, doc_width)
                with col2:
                    self.render_results(model)
            else:
                self.render_doc(model, doc_img, canvas_width, doc_height, doc_width)
        else:
            st.title(model.initial_msg)

    def upload_file(self, uploaded_file):
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

        return os.path.join("docs/inference/", uploaded_file.name)

    def canvas_available_width(self, ui_width, doc_width, device_type, device_width):
        doc_width_pct = (doc_width * 100) / ui_width
        if doc_width_pct < 45:
            canvas_width_pct = 37
        elif doc_width_pct < 55:
            canvas_width_pct = 49
        else:
            canvas_width_pct = 60

        if ui_width > 700 and canvas_width_pct == 37 and device_type == "desktop":
            return math.floor(canvas_width_pct * ui_width / 100), 4
        elif ui_width > 700 and canvas_width_pct == 49 and device_type == "desktop":
            return math.floor(canvas_width_pct * ui_width / 100), 5
        elif ui_width > 700 and canvas_width_pct == 60 and device_type == "desktop":
            return math.floor(canvas_width_pct * ui_width / 100), 6
        else:
            if device_type == "desktop":
                ui_width = device_width - math.floor((device_width * 22) / 100)
            elif device_type == "mobile":
                ui_width = device_width - math.floor((device_width * 13) / 100)
            return ui_width, 1

    def render_doc(self, model, doc_img, canvas_width, doc_height, doc_width):
        with st.container():
            height = 1296
            width = 864

            annotations_json = {
                "meta": {
                    "version": "v0.1",
                    "split": "train",
                    "image_id": 0,
                    "image_size": {
                        "width": doc_width,
                        "height": doc_height
                    }
                },
                "words": []
            }

            st_sparrow_labeling(
                fill_color="rgba(0, 151, 255, 0.3)",
                stroke_width=2,
                stroke_color="rgba(0, 50, 255, 0.7)",
                background_image=doc_img,
                initial_rects=annotations_json,
                height=height,
                width=width,
                drawing_mode="transform",
                display_toolbar=False,
                update_streamlit=False,
                canvas_width=canvas_width,
                doc_height=doc_height,
                doc_width=doc_width,
                image_rescale=True,
                key="doc_annotation" + model.get_image_file()
            )

    def render_results(self, model):
        with st.form(key="results_form"):
            button_placeholder = st.empty()

            submit = button_placeholder.form_submit_button(model.extract_data, type="primary")
            if submit:
                button_placeholder.empty()

                api_url = "https://katanaml-org-sparrow-ml.hf.space/api-inference/v1/sparrow-ml/inference"
                file_path = model.get_image_file()

                with open(file_path, "rb") as file:
                    model_in_use = model.model_in_use
                    sparrow_key = settings.sparrow_key

                    # Prepare the payload
                    files = {
                        'file': (file.name, file, 'image/jpeg')
                    }

                    data = {
                        'image_url': '',
                        'model_in_use': model_in_use,
                        'sparrow_key': sparrow_key
                    }

                    with st.spinner("Extracting data from document..."):
                        response = requests.post(api_url, data=data, files=files)
                if response.status_code != 200:
                    print('Request failed with status code:', response.status_code)
                    print('Response:', response.text)

                model.set_data_result(response.text)

                # Display JSON data in Streamlit
                st.markdown("---")
                st.json(response.text)

                st.experimental_rerun()
            else:
                if model.get_data_result() is not None:
                    st.markdown("---")
                    st.json(model.get_data_result())