import streamlit as st
import numpy as np
import pandas as pd
import os
import json
import altair as alt


class Dashboard:
    class Model:
        pageTitle = "Dashboard"

        documentsTitle = "Pages"
        documentsCount = "10.5K"
        documentsDelta = "125"

        annotationsTitle = "Documents"
        annotationsCount = "510"
        annotationsDelta = "-2"

        accuracyTitle = "Accuracy"
        accuracyCount = "87.9%"
        accuracyDelta = "0.1%"

        trainingTitle = "Training Time"
        trainingCount = "1.5 hrs"
        trainingDelta = "10 mins"

        processingTitle = "Processing Time"
        processingCount = "3 secs"
        processingDelta = "-0.1 secs"

        titleDataExtraction = "## Data Extraction"
        titleModelTraining = "## Model Training"
        titleDataAnnotation = "## Data Annotation"

        status_file = "docs/status.json"
        annotation_files_dir = "docs/json"

    def view(self, model):
        # st.title(model.pageTitle)

        with st.container():
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric(label=model.documentsTitle, value=model.documentsCount, delta=model.documentsDelta)

            with col2:
                st.metric(label=model.annotationsTitle, value=model.annotationsCount, delta=model.annotationsDelta)

            with col3:
                st.metric(label=model.accuracyTitle, value=model.accuracyCount, delta=model.accuracyDelta)

            with col4:
                st.metric(label=model.trainingTitle, value=model.trainingCount, delta=model.trainingDelta, delta_color="inverse")

            with col5:
                st.metric(label=model.processingTitle, value=model.processingCount, delta=model.processingDelta, delta_color="inverse")

            st.markdown("---")


        with st.container():
            st.write(model.titleDataExtraction)
            chart_data = pd.DataFrame(
                np.random.randn(20, 3),
                columns=['a', 'b', 'c'])

            st.line_chart(chart_data)

        st.markdown("---")

        with st.container():
            col1, col2, col3 = st.columns(3)

            with col1:
                with st.container():
                    st.write(model.titleModelTraining)

                    # You can call any Streamlit command, including custom components:
                    st.bar_chart(np.random.randn(50, 3))

            with col2:
                with st.container():
                    st.write(model.titleDataAnnotation)

                    total, completed, in_progress = self.render_annotation_stats(model)

                    source = pd.DataFrame({"Status": ["Completed", "In Progress"], "value": [completed, in_progress]})

                    c = alt.Chart(source).mark_arc().encode(
                        theta=alt.Theta(field="value", type="quantitative"),
                        color=alt.Color(field="Status", type="nominal"),
                    )

                    st.altair_chart(c, use_container_width=True)

    def render_annotation_stats(self, model):
        completed = 0
        in_progress = 0

        files = [f for f in os.listdir(model.annotation_files_dir) if not f.startswith('.')]
        for f in files:
            with open(os.path.join(model.annotation_files_dir, f), "r") as f:
                data = json.load(f)
                v = data['meta']['version']
                if v == 'v0.1':
                    in_progress += 1
                else:
                    completed += 1
        total = completed + in_progress

        status_json = {
            "annotations": [
                {
                    "completed": completed,
                    "in_progress": in_progress,
                    "total": total
                }
            ]
        }

        with open(model.status_file, "w") as f:
            json.dump(status_json, f, indent=2)

        return total, completed, in_progress
