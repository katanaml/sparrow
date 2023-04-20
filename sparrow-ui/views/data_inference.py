import streamlit as st


class DataInference:
    class Model:
        pageTitle = "Data Inference"

    def view(self, model):
        st.title(model.pageTitle)
