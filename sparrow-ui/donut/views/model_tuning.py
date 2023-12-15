import streamlit as st


class ModelTuning:
    class Model:
        pageTitle = "Model Tuning"

    def view(self, model):
        st.title(model.pageTitle)
