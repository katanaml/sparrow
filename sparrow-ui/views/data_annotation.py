import streamlit as st
from PIL import Image
import streamlit_nested_layout
from streamlit_sparrow_labeling import st_sparrow_labeling
from streamlit_sparrow_labeling import DataProcessor
import json
import math


class DataAnnotation:
    class Model:
        pageTitle = "Data Annotation"

        img_file = None
        rects_file = None

        assign_labels_text = "Assign Labels"
        text_caption_1 = "Check 'Assign Labels' to enable editing of labels and values, move and resize the boxes to annotate the document."
        text_caption_2 = "Add annotations by clicking and dragging on the document, when 'Assign Labels' is unchecked."

        labels = ["", "item", "item_price", "subtotal", "tax", "total"]

        selected_field = "Selected Field: "
        save_text = "Save"
        saved_text = "Saved!"

        subheader_1 = "Select"
        subheader_2 = "Upload"
        annotation_text = "Annotation"
        no_annotation_file = "No annotation file selected"
        no_annotation_mapping = "Please annotate the document. Uncheck 'Assign Labels' and draw new annotations"

    def view(self, model, ui_width):
        st.title(model.pageTitle)

        with st.sidebar:
            st.markdown("---")
            st.subheader(model.subheader_1)
            annotation_selection = st.selectbox(
                model.annotation_text,
                ('receipt_00001', 'receipt_00002', 'receipt_00003'))
            model.img_file = f"docs/image/{annotation_selection}.png"
            model.rects_file = f"docs/json/{annotation_selection}.json"

            st.subheader(model.subheader_2)
            st.file_uploader("Choose a file", accept_multiple_files=True)

        if model.img_file is None:
            st.caption(model.no_annotation_file)
            return

        saved_state = self.fetch_annotations(model.rects_file)

        assign_labels = st.checkbox(model.assign_labels_text, True)
        mode = "transform" if assign_labels else "rect"

        docImg = Image.open(model.img_file)

        data_processor = DataProcessor()

        with st.container():
            col1, col2 = st.columns([4, 6])

            with col1:
                with st.container():
                    height = 1296
                    width = 864

                    doc_height = saved_state['meta']['image_size']['height']
                    doc_width = saved_state['meta']['image_size']['width']

                    canvas_width = self.canvas_available_width(ui_width)

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

            with col2:
                with st.container():
                    if result_rects is not None:
                        if len(result_rects.rects_data['words']) == 0:
                            st.caption(model.no_annotation_mapping)
                            return
                        else:
                            st.download_button(label='Download', data=model.img_file)

                        with st.form(key="fields_form"):
                            if result_rects.current_rect_index is not None and result_rects.current_rect_index != -1:
                                st.write(model.selected_field,
                                         result_rects.rects_data['words'][result_rects.current_rect_index]['value'])
                                st.markdown("---")

                            if ui_width > 1500:
                                self.render_form_wide(result_rects.rects_data['words'], model.labels, result_rects,
                                                      data_processor)
                            elif ui_width > 1000:
                                self.render_form_avg(result_rects.rects_data['words'], model.labels, result_rects,
                                                     data_processor)
                            elif ui_width > 500:
                                self.render_form_narrow(result_rects.rects_data['words'], model.labels, result_rects,
                                                        data_processor)
                            else:
                                self.render_form_mobile(result_rects.rects_data['words'], model.labels, result_rects,
                                                        data_processor)

                            submit = st.form_submit_button(model.save_text, type="primary")
                            if submit:
                                with open(model.rects_file, "w") as f:
                                    json.dump(result_rects.rects_data, f, indent=2)
                                with open(model.rects_file, "r") as f:
                                    saved_state = json.load(f)
                                    st.session_state['saved_state'] = saved_state
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

    def canvas_available_width(self, ui_width):
        # Get ~40% of the available width, if the UI is wider than 500px
        if ui_width > 500:
            return math.floor(38 * ui_width / 100)
        else:
            return ui_width

    def fetch_annotations(self, rects_file):
        if rects_file not in st.session_state:
            with open(rects_file, "r") as f:
                saved_state = json.load(f)
                st.session_state[rects_file] = saved_state
        else:
            saved_state = st.session_state[rects_file]

        return saved_state
