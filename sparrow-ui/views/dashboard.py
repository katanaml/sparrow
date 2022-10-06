import streamlit as st
import numpy as np
import pandas as pd


class Dashboard:
    class Model:
        pageTitle = "Dashboard"

    def view(self, model):
        st.title(model.pageTitle)

        with st.container():
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric(label="Documents", value="10.5K", delta="125")

            with col2:
                st.metric(label="Annotations", value="510", delta="-2")

            with col3:
                st.metric(label="Accuracy", value="87.9%", delta="0.1%")

            with col4:
                st.metric(label="Training Time", value="1.5 hours", delta="10 mins", delta_color="inverse")

            with col5:
                st.metric(label="Processing Time", value="3 seconds", delta="-0.1 seconds", delta_color="inverse")

            st.markdown("---")


        with st.container():
            st.write("## Data Extraction")
            chart_data = pd.DataFrame(
                np.random.randn(20, 3),
                columns=['a', 'b', 'c'])

            st.line_chart(chart_data)

        st.markdown("---")

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                with st.container():
                    st.write("## Model Training")

                    # You can call any Streamlit command, including custom components:
                    st.bar_chart(np.random.randn(50, 3))

            with col2:
                with st.container():
                    st.write("## Data Annotation")

                    chart_data = pd.DataFrame(
                        np.random.randn(20, 3),
                        columns=['a', 'b', 'c'])

                    st.area_chart(chart_data)
