import streamlit as st
from natsort import natsorted
import os
from PIL import Image
import math
from streamlit_sparrow_labeling import st_sparrow_labeling
import json


class DataReview:
    class Model:
        # pageTitle = "Data Review"
        subheader_2 = "Select"
        subheader_3 = "Result"
        selection_text = "File to review"
        initial_msg = "Please select a file to review"

        img_file = None

        def set_image_file(self, img_file):
            st.session_state['img_file_review'] = img_file

        def get_image_file(self):
            if 'img_file_review' not in st.session_state:
                return None
            return st.session_state['img_file_review']

        json_file = None

        def set_json_file(self, json_file):
            st.session_state['json_file_review'] = json_file

        def get_json_file(self):
            if 'json_file_review' not in st.session_state:
                return None
            return st.session_state['json_file_review']

    def view(self, model, ui_width, device_type, device_width):
        # st.title(model.pageTitle)

        with st.sidebar:
            st.markdown("---")
            st.subheader(model.subheader_2)

            # get list of files in inference directory
            processed_file_names = self.get_processed_file_names('docs/inference/')

            if 'selection_index' not in st.session_state:
                st.session_state['selection_index'] = 0
                selection_index = 0
            else:
                selection_index = st.session_state['selection_index']

            selection = st.selectbox(model.selection_text, processed_file_names, index=selection_index)

            selection_index = self.get_selection_index(selection, processed_file_names)
            st.session_state['selection_index'] = selection_index

        img_file = "docs/inference/" + selection + ".jpg"
        json_file = "docs/inference/" + selection + ".json"

        model.set_image_file(img_file)
        model.set_json_file(json_file)

        if model.get_image_file() is not None:
            doc_img = Image.open(model.get_image_file())
            doc_height = doc_img.height
            doc_width = doc_img.width

            canvas_width, number_of_columns = self.canvas_available_width(ui_width, doc_width, device_type,
                                                                          device_width)

            if number_of_columns > 1:
                col1, col2 = st.columns([number_of_columns, 10 - number_of_columns])
                with col1:
                    pass
                    self.render_doc(model, doc_img, canvas_width, doc_height, doc_width)
                with col2:
                    pass
                    self.render_results(model)
            else:
                pass
                self.render_doc(model, doc_img, canvas_width, doc_height, doc_width)
                self.render_results(model)
        else:
            st.title(model.initial_msg)


    def get_processed_file_names(self, dir_name):
        # get ordered list of files without file extension, excluding hidden files, with JSON extension only
        file_names = [os.path.splitext(f)[0] for f in os.listdir(dir_name) if
                        os.path.isfile(os.path.join(dir_name, f)) and not f.startswith('.') and f.endswith('.json')]
        file_names = natsorted(file_names)
        return file_names

    def get_selection_index(self, file, files_list):
        return files_list.index(file)

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
        json_file = model.get_json_file()
        if json_file is not None:
            with open(json_file) as f:
                data_json = json.load(f)
                st.subheader(model.subheader_3)
                st.markdown("---")
                st.json(data_json)
                st.markdown("---")