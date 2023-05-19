import streamlit as st
from streamlit_option_menu import option_menu
from tools.utilities import load_css
import json

from views.dashboard import Dashboard
from views.data_annotation import DataAnnotation
from views.model_training import ModelTraining
from views.model_tuning import ModelTuning
from views.data_inference import DataInference
from views.setup import Setup
from views.data_review import DataReview
from views.about import About

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
    option5 = "Inference"
    option6 = "Data Review"
    option7 = "Setup"
    option8 = "About"

    menuIcon = "menu-up"
    icon1 = "speedometer"
    icon2 = "activity"
    icon3 = "motherboard"
    icon4 = "graph-up-arrow"
    icon5 = "journal-arrow-down"
    icon6 = "droplet"
    icon7 = "clipboard-data"
    icon8 = "chat"


def view(model):
    with st.sidebar:
        menuItem = option_menu(model.menuTitle,
                               [model.option1, model.option2, model.option5, model.option6, model.option7, model.option8],
                               icons=[model.icon1, model.icon2, model.icon5, model.icon6, model.icon7, model.icon8],
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
        logout_widget()

    if menuItem == model.option2:
        if 'ui_width' not in st.session_state or 'device_type' not in st.session_state or 'device_width' not in st.session_state:
            # Get UI width
            ui_width = st_js.st_javascript("window.innerWidth", key="ui_width_comp")
            device_width = st_js.st_javascript("window.screen.width", key="device_width_comp")

            if ui_width > 0 and device_width > 0:
                # Add 20% of current screen width to compensate for the sidebar
                ui_width = round(ui_width + (20 * ui_width / 100))

                if device_width > 768:
                    device_type = 'desktop'
                else:
                    device_type = 'mobile'

                st.session_state['ui_width'] = ui_width
                st.session_state['device_type'] = device_type
                st.session_state['device_width'] = device_width

                st.experimental_rerun()
        else:
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
        if 'ui_width' not in st.session_state or 'device_type' not in st.session_state or 'device_width' not in st.session_state:
            # Get UI width
            ui_width = st_js.st_javascript("window.innerWidth", key="ui_width_comp")
            device_width = st_js.st_javascript("window.screen.width", key="device_width_comp")

            if ui_width > 0 and device_width > 0:
                # Add 20% of current screen width to compensate for the sidebar
                ui_width = round(ui_width + (20 * ui_width / 100))

                if device_width > 768:
                    device_type = 'desktop'
                else:
                    device_type = 'mobile'

                st.session_state['ui_width'] = ui_width
                st.session_state['device_type'] = device_type
                st.session_state['device_width'] = device_width

                st.experimental_rerun()
        else:
            DataInference().view(DataInference.Model(), st.session_state['ui_width'], st.session_state['device_type'],
                                 st.session_state['device_width'])

        logout_widget()

    if menuItem == model.option6:
        if 'ui_width' not in st.session_state or 'device_type' not in st.session_state or 'device_width' not in st.session_state:
            # Get UI width
            ui_width = st_js.st_javascript("window.innerWidth", key="ui_width_comp")
            device_width = st_js.st_javascript("window.screen.width", key="device_width_comp")

            if ui_width > 0 and device_width > 0:
                # Add 20% of current screen width to compensate for the sidebar
                ui_width = round(ui_width + (20 * ui_width / 100))

                if device_width > 768:
                    device_type = 'desktop'
                else:
                    device_type = 'mobile'

                st.session_state['ui_width'] = ui_width
                st.session_state['device_type'] = device_type
                st.session_state['device_width'] = device_width

                st.experimental_rerun()
        else:
            DataReview().view(DataReview.Model(), st.session_state['ui_width'], st.session_state['device_type'],
                              st.session_state['device_width'])

        logout_widget()

    if menuItem == model.option7:
        Setup().view(Setup.Model())
        logout_widget()

    if menuItem == model.option8:
        About().view(About.Model())
        logout_widget()


def logout_widget():
    with st.sidebar:
        st.markdown("---")
        # st.write("User:", "John Doe")
        st.write("Version:", "2.0.0")
        # st.button("Logout")
        # st.markdown("---")

        if 'visitors' not in st.session_state:
            with open("docs/visitors.json", "r") as f:
                visitors_json = json.load(f)
                visitors = visitors_json["meta"]["visitors"]

            visitors += 1
            visitors_json["meta"]["visitors"] = visitors

            with open("docs/visitors.json", "w") as f:
                json.dump(visitors_json, f)

            st.session_state['visitors'] = visitors
        else:
            visitors = st.session_state['visitors']

        st.write("Counter:", visitors)


view(Model())
