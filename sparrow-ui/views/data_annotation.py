import streamlit as st
from PIL import Image
import streamlit_nested_layout
from streamlit_sparrow_labeling import st_sparrow_labeling
from streamlit_sparrow_labeling import DataProcessor
import json
import math
import os


class DataAnnotation:
    class Model:
        pageTitle = "Data Annotation"

        img_file = None
        rects_file = None

        assign_labels_text = "Assign Labels"
        text_caption_1 = "Check 'Assign Labels' to enable editing of labels and values, move and resize the boxes to annotate the document."
        text_caption_2 = "Add annotations by clicking and dragging on the document, when 'Assign Labels' is unchecked."

        labels = ["", "item", "item_price", "subtotal", "tax", "total", "date_issued", "due_date", "invoice_number",
                  "amount_due", "deposit_due"]

        selected_field = "Selected Field: "
        save_text = "Save"
        saved_text = "Saved!"

        subheader_1 = "Select"
        subheader_2 = "Upload"
        annotation_text = "Annotation"
        no_annotation_file = "No annotation file selected"
        no_annotation_mapping = "Please annotate the document. Uncheck 'Assign Labels' and draw new annotations"

        download_text = "Download"
        download_hint = "Download the annotated structure in JSON format"

        annotation_selection_help = "Select an annotation file to load"
        upload_help = "Upload a file to annotate"
        upload_button_text = "Upload"
        upload_button_text_desc = "Choose a file"

        assign_labels_text = "Assign Labels"
        assign_labels_help = "Check to enable editing of labels and values"
        save_help = "Save the annotations"

    def view(self, model, ui_width, device_type, device_width):
        with st.sidebar:
            st.markdown("---")
            st.subheader(model.subheader_1)

            placeholder_upload = st.empty()

            file_names = self.get_existing_file_names('docs/image/')

            if 'annotation_index' not in st.session_state:
                st.session_state['annotation_index'] = 0
                annotation_index = 0
            else:
                annotation_index = st.session_state['annotation_index']

            annotation_selection = placeholder_upload.selectbox(model.annotation_text, file_names,
                                                                index=annotation_index,
                                                                help=model.annotation_selection_help)
            annotation_index = self.get_annotation_index(annotation_selection, file_names)
            st.session_state['annotation_index'] = annotation_index

            file_extension = self.get_file_extension(annotation_selection, 'docs/image/')
            model.img_file = f"docs/image/{annotation_selection}" + file_extension
            model.rects_file = f"docs/json/{annotation_selection}.json"

            st.subheader(model.subheader_2)

            with st.form("upload-form", clear_on_submit=True):
                uploaded_file = st.file_uploader(model.upload_button_text_desc, accept_multiple_files=False,
                                                 type=['png', 'jpg', 'jpeg'],
                                                 help=model.upload_help)
                submitted = st.form_submit_button(model.upload_button_text)

                if submitted and uploaded_file is not None:
                    ret = self.upload_file(uploaded_file)

                    if ret is not False:
                        file_names = self.get_existing_file_names('docs/image/')

                        annotation_index = self.get_annotation_index(annotation_selection, file_names)
                        annotation_selection = placeholder_upload.selectbox(model.annotation_text, file_names,
                                                                            index=annotation_index,
                                                                            help=model.annotation_selection_help)
                        st.session_state['annotation_index'] = annotation_index

        st.title(model.pageTitle + " - " + annotation_selection)

        if model.img_file is None:
            st.caption(model.no_annotation_file)
            return

        saved_state = self.fetch_annotations(model.rects_file)

        assign_labels = st.checkbox(model.assign_labels_text, True, help=model.assign_labels_help)
        mode = "transform" if assign_labels else "rect"

        docImg = Image.open(model.img_file)

        data_processor = DataProcessor()

        with st.container():
            doc_height = saved_state['meta']['image_size']['height']
            doc_width = saved_state['meta']['image_size']['width']
            canvas_width, number_of_columns = self.canvas_available_width(ui_width, doc_width, device_type,
                                                                          device_width)

            if number_of_columns > 1:
                col1, col2 = st.columns([number_of_columns, 10 - number_of_columns])
                with col1:
                    result_rects = self.render_doc(model, docImg, saved_state, mode, canvas_width, doc_height, doc_width)
                with col2:
                    self.render_form(model, result_rects, data_processor, number_of_columns, annotation_selection)
            else:
                result_rects = self.render_doc(model, docImg, saved_state, mode, canvas_width, doc_height, doc_width)
                self.render_form(model, result_rects, data_processor, number_of_columns, annotation_selection)

    def render_doc(self, model, docImg, saved_state, mode, canvas_width, doc_height, doc_width):
        with st.container():
            height = 1296
            width = 864

            result_rects = st_sparrow_labeling(
                fill_color="rgba(0, 151, 255, 0.3)",
                stroke_width=2,
                stroke_color="rgba(0, 50, 255, 0.7)",
                background_image=docImg,
                initial_rects=saved_state,
                height=height,
                width=width,
                drawing_mode=mode,
                display_toolbar=True,
                update_streamlit=True,
                canvas_width=canvas_width,
                doc_height=doc_height,
                doc_width=doc_width,
                image_rescale=True,
                key="doc_annotation" + model.img_file
            )

            st.caption(model.text_caption_1)
            st.caption(model.text_caption_2)

            return result_rects

    def render_form(self, model, result_rects, data_processor, number_of_columns, annotation_selection):
        with st.container():
            if result_rects is not None:
                if len(result_rects.rects_data['words']) == 0:
                    st.caption(model.no_annotation_mapping)
                    return
                else:
                    with open(model.rects_file, 'rb') as file:
                        st.download_button(label=model.download_text,
                                           data=file,
                                           file_name=annotation_selection + ".json",
                                           mime='application/json',
                                           help=model.download_hint)

                with st.form(key="fields_form"):
                    if result_rects.current_rect_index is not None and result_rects.current_rect_index != -1:
                        st.write(model.selected_field,
                                 result_rects.rects_data['words'][result_rects.current_rect_index]['value'])
                        st.markdown("---")

                    if number_of_columns == 4:
                        self.render_form_wide(result_rects.rects_data['words'], model.labels, result_rects,
                                              data_processor)
                    elif number_of_columns == 5:
                        self.render_form_avg(result_rects.rects_data['words'], model.labels, result_rects,
                                             data_processor)
                    elif number_of_columns == 6:
                        self.render_form_narrow(result_rects.rects_data['words'], model.labels, result_rects,
                                                data_processor)
                    else:
                        self.render_form_mobile(result_rects.rects_data['words'], model.labels, result_rects,
                                                data_processor)

                    submit = st.form_submit_button(model.save_text, type="primary", help=model.save_help)
                    if submit:
                        with open(model.rects_file, "w") as f:
                            json.dump(result_rects.rects_data, f, indent=2)
                        st.session_state[model.rects_file] = result_rects.rects_data
                        st.write(model.saved_text)

    def render_form_wide(self, words, labels, result_rects, data_processor):
        col1_form, col2_form, col3_form, col4_form = st.columns([1, 1, 1, 1])
        num_rows = math.ceil(len(words) / 4)

        for i, rect in enumerate(words):
            if i < num_rows:
                with col1_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)
            elif i < num_rows * 2:
                with col2_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)
            elif i < num_rows * 3:
                with col3_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)
            else:
                with col4_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)

    def render_form_avg(self, words, labels, result_rects, data_processor):
        col1_form, col2_form, col3_form = st.columns([1, 1, 1])
        num_rows = math.ceil(len(words) / 3)

        for i, rect in enumerate(words):
            if i < num_rows:
                with col1_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)
            elif i < num_rows * 2:
                with col2_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)
            else:
                with col3_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)

    def render_form_narrow(self, words, labels, result_rects, data_processor):
        col1_form, col2_form = st.columns([1, 1])
        num_rows = math.ceil(len(words) / 2)

        for i, rect in enumerate(words):
            if i < num_rows:
                with col1_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)
            else:
                with col2_form:
                    self.render_form_element(rect, labels, i, result_rects, data_processor)

    def render_form_mobile(self, words, labels, result_rects, data_processor):
        for i, rect in enumerate(words):
            self.render_form_element(rect, labels, i, result_rects, data_processor)

    def render_form_element(self, rect, labels, i, result_rects, data_processor):
        default_index = 0
        if rect['label']:
            default_index = labels.index(rect['label'])

        value = st.text_input("Value", rect['value'], key=f"field_value_{i}",
                              disabled=False if i == result_rects.current_rect_index else True)
        label = st.selectbox("Label", labels, key=f"label_{i}", index=default_index,
                             disabled=False if i == result_rects.current_rect_index else True)
        st.markdown("---")

        data_processor.update_rect_data(result_rects.rects_data, i, value, label)

    def canvas_available_width(self, ui_width, doc_width, device_type, device_width):
        doc_width_pct = (doc_width * 100) / ui_width
        if doc_width_pct < 45:
            canvas_width_pct = 37
        elif doc_width_pct < 55:
            canvas_width_pct = 49
        else:
            canvas_width_pct = 65

        if ui_width > 700 and canvas_width_pct == 37 and device_type == "desktop":
            return math.floor(canvas_width_pct * ui_width / 100), 4
        elif ui_width > 700 and canvas_width_pct == 49 and device_type == "desktop":
            return math.floor(canvas_width_pct * ui_width / 100), 5
        elif ui_width > 700 and canvas_width_pct == 65 and device_type == "desktop":
            return math.floor(canvas_width_pct * ui_width / 100), 6
        else:
            if device_type == "desktop":
                ui_width = device_width - math.floor((device_width * 22) / 100)
            elif device_type == "mobile":
                ui_width = device_width - math.floor((device_width * 13) / 100)
            return ui_width, 1

    def fetch_annotations(self, rects_file):
        if rects_file not in st.session_state:
            with open(rects_file, "r") as f:
                saved_state = json.load(f)
                st.session_state[rects_file] = saved_state
        else:
            saved_state = st.session_state[rects_file]

        return saved_state

    def upload_file(self, uploaded_file):
        if uploaded_file is not None:
            if os.path.exists(os.path.join("docs/image/", uploaded_file.name)):
                st.write("File already exists")
                return False

            with open(os.path.join("docs/image/", uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())

            img_file = Image.open(os.path.join("docs/image/", uploaded_file.name))

            annotations_json = {
                "meta": {
                    "version": "v0.1",
                    "split": "train",
                    "image_id": len(self.get_existing_file_names("docs/image/")),
                    "image_size": {
                        "width": img_file.width,
                        "height": img_file.height
                    }
                },
                "words": []
            }

            file_name = uploaded_file.name.split(".")[0]
            with open(os.path.join("docs/json/", file_name + ".json"), "w") as f:
                json.dump(annotations_json, f, indent=2)

            st.write("File uploaded successfully")

    def get_existing_file_names(self, dir_name):
        # get ordered list of files without file extension, excluding hidden files
        return sorted([os.path.splitext(f)[0] for f in os.listdir(dir_name) if not f.startswith('.')])

    def get_file_extension(self, file_name, dir_name):
        # get list of files, excluding hidden files
        files = [f for f in os.listdir(dir_name) if not f.startswith('.')]
        for f in files:
            if file_name is not  None and os.path.splitext(f)[0] == file_name:
                return os.path.splitext(f)[1]

    def get_annotation_index(self, file, files_list):
        return files_list.index(file)

