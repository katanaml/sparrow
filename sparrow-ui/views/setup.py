import streamlit as st
import json
import pandas as pd
from tools import agstyler
from tools.agstyler import PINLEFT


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

        st.button("Create")
        st.button("Delete")
        st.button("Save", type="primary")

        response = agstyler.draw_grid(
            df,
            formatter=formatter,
            fit_columns=True,
            pagination_size=30,
            selection="single",
            use_checkbox=False
        )
