import streamlit as st


class Dashboard:
    class Model:
        pageTitle = "Dashboard"

    def view(self, model):
        st.title(model.pageTitle)
