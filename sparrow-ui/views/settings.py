import streamlit as st


class Settings:
    class Model:
        pageTitle = "Settings"

    def view(self, model):
        st.title(model.pageTitle)
