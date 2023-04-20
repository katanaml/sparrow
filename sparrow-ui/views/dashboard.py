import streamlit as st
import numpy as np
import pandas as pd
import json
import altair as alt
from pathlib import Path
import requests


class Dashboard:
    class Model:
        pageTitle = "Dashboard"

        wordsTitle = "Words"

        inferenceTimeTitle = "Inference Time"

        documentsTitle = "Documents"

        dailyInferenceTitle = "Top Daily Inference"

        trainingLossTitle = "Training Loss"

        titleTrainingLoss = "## Training Loss"
        titleInferencePerformance = "## Inference Performance"
        titleDatasetInfo = "## Dataset Info"
        titleDataAnnotation = "## Data Annotation"
        titleTrainingPerformance = "## Training Performance"

        status_file = "docs/status.json"
        annotation_files_dir = "docs/json"

    def view(self, model):
        # st.title(model.pageTitle)

        api_url = "https://katanaml-org-sparrow-ml.hf.space/api-inference/v1/sparrow-ml/statistics"
        json_data_inference = []
        response = requests.get(api_url)
        if response.status_code == 200:
            json_data_inference = response.json()
        else:
            print(f"Error: Unable to fetch data from the API (status code {response.status_code})")

        api_url_t = "https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/statistics"
        json_data_training = []
        response_t = requests.get(api_url_t)
        if response_t.status_code == 200:
            json_data_training = response_t.json()
        else:
            print(f"Error: Unable to fetch data from the API (status code {response_t.status_code})")

        with st.container():
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                words_count = 0
                delta_words = 0

                if len(json_data_inference) > 3:
                    for i in range(0, len(json_data_inference)):
                        words_count = words_count + json_data_inference[i][1]

                    avg_word_count = words_count / len(json_data_inference)
                    avg_word_last = (json_data_inference[len(json_data_inference) - 1][1]
                                     + json_data_inference[len(json_data_inference) - 2][1] +
                                     json_data_inference[len(json_data_inference) - 3][1]) / 3

                    if avg_word_last >= avg_word_count:
                        delta_words = round(100 - ((avg_word_count * 100) / avg_word_last), 2)
                    else:
                        delta_words = round(100 - ((avg_word_last * 100) / avg_word_count), 2) * -1

                    words_count = words_count / 1000
                st.metric(label=model.wordsTitle, value=str(words_count) + 'K', delta=str(delta_words) + "%")

            with col2:
                docs_count = len(json_data_inference)
                delta_docs = 0

                if docs_count > 3:
                    inference_dates = []
                    for i in range(0, len(json_data_inference)):
                        inference_dates.append(json_data_inference[i][4].split(" ")[0])

                    inference_dates_unique = []
                    for item in inference_dates:
                        if item not in inference_dates_unique:
                            inference_dates_unique.append(item)

                    if len(inference_dates_unique) > 3:
                        inference_dates_dict = {}
                        for i, key in enumerate(inference_dates_unique):
                            inference_dates_dict[key] = [0]

                        for i in range(0, len(json_data_inference)):
                            inference_dates_dict[json_data_inference[i][4].split(" ")[0]][0] = \
                                inference_dates_dict[json_data_inference[i][4].split(" ")[0]][0] + 1

                        # calculate average for values from inference_dates_dict
                        avg_value = 0
                        for key, value in inference_dates_dict.items():
                            avg_value = avg_value + value[0]
                        avg_value = round(avg_value / len(inference_dates_dict), 2)

                        # calculate average for last 3 values from inference_dates_dict
                        avg_value_last = 0
                        for i in range(1, 4):
                            avg_value_last = avg_value_last + inference_dates_dict[inference_dates_unique[len(inference_dates_unique) - i]][0]
                        avg_value_last = round(avg_value_last / 3, 2)

                        if avg_value_last > avg_value:
                            delta_docs = round(100 - ((avg_value * 100) / avg_value_last), 2)
                        else:
                            delta_docs = round(100 - ((avg_value_last * 100) / avg_value), 2) * -1

                st.metric(label=model.documentsTitle, value=docs_count, delta=str(delta_docs) + "%")

            with col3:
                inference_dates = []
                for i in range(0, len(json_data_inference)):
                    inference_dates.append(json_data_inference[i][4].split(" ")[0])

                inference_dates_unique = []
                for item in inference_dates:
                    if item not in inference_dates_unique:
                        inference_dates_unique.append(item)

                inference_dates_dict = {}
                for i, key in enumerate(inference_dates_unique):
                    inference_dates_dict[key] = [0]

                for i in range(0, len(json_data_inference)):
                    inference_dates_dict[json_data_inference[i][4].split(" ")[0]][0] = \
                        inference_dates_dict[json_data_inference[i][4].split(" ")[0]][0] + 1

                # loop through the dictionary and find the max value
                max_value = 0
                for key, value in inference_dates_dict.items():
                    if value[0] > max_value:
                        max_value = value[0]

                # calculate average for values from inference_dates_dict
                avg_value = 0
                for key, value in inference_dates_dict.items():
                    avg_value = avg_value + value[0]
                avg_value = round(avg_value / len(inference_dates_dict), 2)

                avg_delta = round(100 - ((avg_value * 100) / max_value), 2)

                st.metric(label=model.dailyInferenceTitle, value=max_value, delta=str(avg_delta) + "%")

            with col4:
                inference_time_avg = 0

                # calculate inference time average
                for i in range(0, len(json_data_inference)):
                    inference_time_avg = inference_time_avg + json_data_inference[i][0]
                inference_time_avg = round(inference_time_avg / len(json_data_inference), 2)

                delta_time = 0
                if len(json_data_inference) > 3:
                    avg_time_last = (json_data_inference[len(json_data_inference) - 1][0] +
                                     json_data_inference[len(json_data_inference) - 2][0] +
                                     json_data_inference[len(json_data_inference) - 3][0]) / 3

                    if avg_time_last > inference_time_avg:
                        delta_time = round(100 - ((inference_time_avg * 100) / avg_time_last), 2)
                    else:
                        delta_time = round(100 - ((avg_time_last * 100) / inference_time_avg), 2) * -1

                st.metric(label=model.inferenceTimeTitle, value=str(inference_time_avg) + " s", delta=str(delta_time) + "%",
                          delta_color="inverse")

            with col5:
                training_loss_avg = 0

                # calculate training loss average
                for i in range(0, len(json_data_training)):
                    training_loss_avg = training_loss_avg + json_data_training[i][1]
                training_loss_avg = round(training_loss_avg / len(json_data_training), 2)

                delta_loss = 0
                if len(json_data_training) > 5:
                    # calculate training loss average for last 3 values
                    training_loss_avg_last = (json_data_training[len(json_data_training) - 1][1] +
                                                json_data_training[len(json_data_training) - 2][1] +
                                                json_data_training[len(json_data_training) - 3][1]) / 3

                    if training_loss_avg_last > training_loss_avg:
                        delta_loss = round(100 - ((training_loss_avg * 100) / training_loss_avg_last), 2)
                    else:
                        delta_loss = round(100 - ((training_loss_avg_last * 100) / training_loss_avg), 2) * -1

                st.metric(label=model.trainingLossTitle, value=training_loss_avg, delta=str(delta_loss) + "%",
                          delta_color="inverse")

            st.markdown("---")


        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                st.write(model.titleInferencePerformance)

                models_dict = {}

                models = []
                for i in range(0, len(json_data_inference)):
                    models.append(json_data_inference[i][3])

                models_unique = []
                for item in models:
                    if item not in models_unique:
                        models_unique.append(item)

                for i, key in enumerate(models_unique):
                    models_dict[key] = []

                for i in range(0, len(json_data_inference)):
                    models_dict[json_data_inference[i][3]].append(round(json_data_inference[i][0]))

                data = pd.DataFrame(models_dict)
                st.line_chart(data)

            with col2:
                st.write(model.titleTrainingLoss)

                models_dict = {}

                models = []
                for i in range(0, len(json_data_training)):
                    models.append(json_data_training[i][3])

                models_unique = []
                for item in models:
                    if item not in models_unique:
                        models_unique.append(item)

                for i, key in enumerate(models_unique):
                    models_dict[key] = []

                for i in range(0, len(json_data_training)):
                    models_dict[json_data_training[i][3]].append(json_data_training[i][1])

                data = pd.DataFrame(models_dict)
                st.line_chart(data)

        st.markdown("---")

        with st.container():
            col1, col2, col3 = st.columns(3)

            with col1:
                with st.container():
                    st.write(model.titleDataAnnotation)

                    total, completed, in_progress = self.calculate_annotation_stats(model)

                    data = pd.DataFrame({"Status": ["Completed", "In Progress"], "Value": [completed, in_progress]})

                    # Create a horizontal bar chart
                    chart = alt.Chart(data).mark_bar().encode(
                        x='Value:Q',
                        y=alt.Y('Status:N', sort='-x'),
                        color=alt.Color('Status:N', legend=None)
                    )

                    st.altair_chart(chart)
            with col2:
                with st.container():
                    st.write(model.titleDatasetInfo)

                    api_url = "https://katanaml-org-sparrow-data.hf.space/api-dataset/v1/sparrow-data/dataset_info"

                    # Make the GET request
                    response = requests.get(api_url)

                    # Check if the request was successful (status code 200)
                    names = []
                    rows = []
                    if response.status_code == 200:
                        # Convert the response content to a JSON object
                        json_data = response.json()

                        for i in range(0, len(json_data['splits'])):
                            names.append(json_data['splits'][i]['name'])
                            rows.append(json_data['splits'][i]['number_of_rows'])
                    else:
                        print(f"Error: Unable to fetch data from the API (status code {response.status_code})")

                    data = pd.DataFrame({"Dataset": names, "Value": rows})

                    # Create a horizontal bar chart
                    chart = alt.Chart(data).mark_bar().encode(
                        x='Value:Q',
                        y=alt.Y('Dataset:N', sort='-x'),
                        color=alt.Color('Dataset:N', legend=None)
                    )

                    st.altair_chart(chart)
            with col3:
                with st.container():
                    st.write(model.titleTrainingPerformance)

                    models_dict = {}

                    models = []
                    for i in range(0, len(json_data_training)):
                        models.append(json_data_training[i][3])

                    models_unique = []
                    for item in models:
                        if item not in models_unique:
                            models_unique.append(item)

                    for i, key in enumerate(models_unique):
                        models_dict[key] = []

                    for i in range(0, len(json_data_training)):
                        models_dict[json_data_training[i][3]].append(json_data_training[i][2])

                    for key in models_dict:
                        models_dict[key] = round((sum(models_dict[key]) / len(models_dict[key])) / 60)

                    data = pd.DataFrame({"Models": models_dict.keys(), "Value": list(models_dict.values())})

                    # Create a horizontal bar chart
                    chart = alt.Chart(data).mark_bar().encode(
                        x='Value:Q',
                        y=alt.Y('Models:N', sort='-x'),
                        color=alt.Color('Models:N', legend=None)
                    )

                    st.altair_chart(chart)


    def calculate_annotation_stats(self, model):
        completed = 0
        in_progress = 0
        data_dir_path = Path(model.annotation_files_dir)

        for file_name in data_dir_path.glob("*.json"):
            with open(file_name, "r") as f:
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
