import streamlit as st


class ModelTraining:
    class Model:
        pageTitle = "Model Training"

    def view(self, model):
        st.title(model.pageTitle)
