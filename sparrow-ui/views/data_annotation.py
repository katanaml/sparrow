import streamlit as st


class DataAnnotation:
    class Model:
        pageTitle = "Data Annotation"

        titleDocuments = "Document"
        titleFields = "Fields"

    def view(self, model):
        st.title(model.pageTitle)

        with st.container():
            col1, col2 = st.columns([4, 6])

            with col1:
                with st.container():
                    st.subheader(model.titleDocuments)


            with col2:
                with st.container():
                    st.subheader(model.titleFields)
