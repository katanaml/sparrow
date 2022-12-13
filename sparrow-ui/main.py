import streamlit as st
from streamlit_option_menu import option_menu
from tools.utilities import load_css

from views.dashboard import Dashboard
from views.data_annotation import DataAnnotation
from views.model_training import ModelTraining
from views.model_tuning import ModelTuning
from views.data_extraction import DataExtraction
from views.settings import Settings
from views.social import Social

import streamlit_javascript as st_js

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
    option7 = "Social"

    menuIcon = "menu-up"
    icon1 = "speedometer"
    icon2 = "activity"
    icon3 = "motherboard"
    icon4 = "graph-up-arrow"
    icon5 = "clipboard-data"
    icon6 = "gear"
    icon7 = "chat"


def view(model):
    with st.sidebar:
        menuItem = option_menu(model.menuTitle,
                               [model.option1, model.option2, model.option3, model.option4, model.option5,
                                model.option6, model.option7],
                               icons=[model.icon1, model.icon2, model.icon3, model.icon4, model.icon5, model.icon6,
                                      model.icon7],
                               menu_icon=model.menuIcon,
                               default_index=0,
                               styles={
                                   "container": {"padding": "5!important", "background-color": "#fafafa"},
                                   "icon": {"color": "black", "font-size": "25px"},
                                   "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                                "--hover-color": "#eee"},
                                   "nav-link-selected": {"background-color": "#037ffc"},
                               })

    if menuItem == model.option1:
        Dashboard().view(Dashboard.Model())
        ui_width = st_js.st_javascript("window.innerWidth")
        # Add 20% of current screen width to compensate for the sidebar
        ui_width = round(ui_width + (20 * ui_width / 100))

        device_type = st_js.st_javascript("window.screen.width > 768 ? 'desktop' : 'mobile'")
        device_width = st_js.st_javascript("window.screen.width")

        st.session_state['ui_width'] = ui_width
        st.session_state['device_type'] = device_type
        st.session_state['device_width'] = device_width
        logout_widget()

    if menuItem == model.option2:
        DataAnnotation().view(DataAnnotation.Model(), st.session_state['ui_width'], st.session_state['device_type'],
                              st.session_state['device_width'])
        logout_widget()

    if menuItem == model.option3:
        ModelTraining().view(ModelTraining.Model())
        logout_widget()

    if menuItem == model.option4:
        ModelTuning().view(ModelTuning.Model())
        logout_widget()

    if menuItem == model.option5:
        DataExtraction().view(DataExtraction.Model())
        logout_widget()

    if menuItem == model.option6:
        Settings().view(Settings.Model())
        logout_widget()

    if menuItem == model.option7:
        Social().view(Social.Model())
        logout_widget()


def logout_widget():
    with st.sidebar:
        st.markdown("---")
        st.text("User: John Doe")
        st.text("Version: 0.0.1")
        st.button("Logout")
        st.markdown("---")
        st.write("Counter: ", 1546)


view(Model())
