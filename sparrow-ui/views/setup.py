import streamlit as st


class Setup:
    class Model:
        pageTitle = "Setup"

    def view(self, model):
        st.title(model.pageTitle)
