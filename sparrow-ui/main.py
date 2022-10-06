import streamlit as st
from streamlit_option_menu import option_menu
from tools.utilities import load_css

from views.dashboard import Dashboard
from views.data_annotation import DataAnnotation
from views.model_training import ModelTraining
from views.model_tuning import ModelTuning
from views.data_extraction import DataExtraction
from views.settings import Settings

st.set_page_config(
    page_title="Sparrow",
    page_icon="favicon.ico",
    layout="wide"
)

load_css()


class Model:
    menuTitle = "Sparrow"
    option1 = "Dashboard"
    option2 = "Data Annotation"
    option3 = "Model Training"
    option4 = "Model Tuning"
    option5 = "Data Extraction"
    option6 = "Settings"

    menuIcon = "menu-up"
    icon1 = "speedometer"
    icon2 = "activity"
    icon3 = "motherboard"
    icon4 = "graph-up-arrow"
    icon5 = "clipboard-data"
    icon6 = "gear"


def view(model):
    with st.sidebar:
        menuItem = option_menu(model.menuTitle,
                               [model.option1, model.option2, model.option3, model.option4, model.option5,
                                model.option6],
                               icons=[model.icon1, model.icon2, model.icon3, model.icon4, model.icon5, model.icon6],
                               menu_icon=model.menuIcon,
                               default_index=0,
                               styles={
                                   "container": {"padding": "5!important", "background-color": "#fafafa"},
                                   "icon": {"color": "black", "font-size": "25px"},
                                   "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                                "--hover-color": "#eee"},
                                   "nav-link-selected": {"background-color": "#037ffc"},
                               })

    with st.sidebar:
        st.markdown("---")
        st.text("User: John Doe")
        st.text("Version: 0.0.1")
        st.button("Logout")
        st.markdown("---")

    if menuItem == model.option1:
        Dashboard().view(Dashboard.Model())

    if menuItem == model.option2:
        DataAnnotation().view(DataAnnotation.Model())

    if menuItem == model.option3:
        ModelTraining().view(ModelTraining.Model())

    if menuItem == model.option4:
        ModelTuning().view(ModelTuning.Model())

    if menuItem == model.option5:
        DataExtraction().view(DataExtraction.Model())

    if menuItem == model.option6:
        Settings().view(Settings.Model())


view(Model())
