import streamlit as st


class DataAnnotation:
    class Model:
        pageTitle = "Data Annotation"

    def view(self, model):
        st.title(model.pageTitle)
