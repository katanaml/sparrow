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
        self.action_event = False
        if 'action' not in st.session_state:
            st.session_state['action'] = None

        with open(model.labels_file, "r") as f:
            labels_json = json.load(f)

        labels = labels_json["labels"]

        data = []
        for label in labels:
            data.append({'id': label['id'], 'name': label['name'], 'description': label['description']})
        self.df = pd.DataFrame(data)

        formatter = {
            'id': ('ID', {'hide': True}),
            'name': ('Label', {**PINLEFT, 'editable': True}),
            'description': ('Description', {**PINLEFT, 'editable': True})
        }

        def run_component(props):
            value = component_toolbar_buttons(key='toolbar_buttons', **props)
            return value

        def handle_event(value):
            if value is not None:
                if 'action_timestamp' not in st.session_state:
                    self.action_event = True
                    st.session_state['action_timestamp'] = value['timestamp']
                else:
                    if st.session_state['action_timestamp'] != value['timestamp']:
                        self.action_event = True
                        st.session_state['action_timestamp'] = value['timestamp']
                    else:
                        self.action_event = False

            if value is not None and value['action'] == 'create' and self.action_event:
                if st.session_state['action'] != 'delete':
                    max_id = self.df['id'].max()
                    self.df.loc[-1] = [max_id + 1, '', '']  # adding a row
                    self.df.index = self.df.index + 1  # shifting index
                    self.df.sort_index(inplace=True)
                    st.session_state['action'] = 'create'
            elif value is not None and value['action'] == 'delete' and self.action_event:
                if st.session_state['action'] != 'delete' and st.session_state['action'] != 'create':
                    rows = st.session_state['selected_rows']
                    if len(rows) > 0:
                        idx = rows[0]['_selectedRowNodeInfo']['nodeRowIndex']
                        self.df.drop(self.df.index[idx], inplace=True)
                        self.df.reset_index(drop=True, inplace=True)
                    st.session_state['action'] = 'delete'
            elif value is not None and value['action'] == 'save' and self.action_event:
                st.session_state['action'] = 'save'

        props = {
            'buttons': {
                'create': False,
                'delete': False,
                'save': False,
            }
        }

        handle_event(run_component(props))

        if st.session_state['action'] == 'save' and 'response' in st.session_state:
            if st.session_state['response'] is not None:
                self.df = st.session_state['response']
            st.session_state['response'] = None

        if st.session_state['action'] == 'create' and 'response' in st.session_state:
            if st.session_state['response'] is not None:
                self.df = st.session_state['response']

        if st.session_state['action'] == 'delete' and 'response' in st.session_state:
            if st.session_state['response'] is not None:
                self.df = st.session_state['response']

        response = agstyler.draw_grid(
            self.df,
            formatter=formatter,
            fit_columns=True,
            pagination_size=10,
            selection="single",
            use_checkbox=False
        )

        rows = response['selected_rows']
        st.session_state['selected_rows'] = rows

        if st.session_state['action'] == 'create' and self.action_event:
            st.session_state['response'] = response['data']
        elif st.session_state['action'] == 'delete' and self.action_event:
            st.session_state['response'] = response['data']
        elif st.session_state['action'] == 'save' and self.action_event:
            data = response['data'].values.tolist()
            rows = []
            for row in data:
                rows.append({'id': row[0], 'name': row[1], 'description': row[2]})

            labels_json['labels'] = rows
            with open(model.labels_file, "w") as f:
                json.dump(labels_json, f, indent=2)
