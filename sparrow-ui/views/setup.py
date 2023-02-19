import streamlit as st
import json
import pandas as pd
from tools import agstyler
from tools.agstyler import PINLEFT
from toolbar import component_toolbar_buttons


class Setup:
    class Model:
        pageTitle = "Labels"

        labels_file = "docs/labels.json"

    def view(self, model):
        st.title(model.pageTitle)

        self.setup_labels(model)

    def setup_labels(self, model):
        with open(model.labels_file, "r") as f:
            labels_json = json.load(f)

        labels = labels_json["labels"]

        data = []
        for label in labels:
            data.append({'id': label['id'], 'name': label['name'], 'description': label['description']})
        df = pd.DataFrame(data)

        formatter = {
            'id': ('ID', {'hide': True}),
            'name': ('Label', {**PINLEFT, 'editable': True}),
            'description': ('Description', {**PINLEFT, 'editable': True})
        }

        def run_component(props):
            value = component_toolbar_buttons(key='toolbar_buttons', **props)
            return value

        def handle_event(value):
            st.write('Received from component: ', value)

        props = {
            'buttons': {
                'create': False,
                'delete': False,
                'save': False,
            }
        }

        handle_event(run_component(props))

        response = agstyler.draw_grid(
            df,
            formatter=formatter,
            fit_columns=True,
            pagination_size=10,
            selection="single",
            use_checkbox=False
        )
