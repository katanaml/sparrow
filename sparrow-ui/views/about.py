import streamlit as st
from PIL import Image
from tools.st_functions import st_button


class About:
    class Model:
        pageTitle = "About"

    def view(self, model):
        st.title(model.pageTitle)

        st.write(
            "[![Star](https://img.shields.io/github/stars/katanaml/sparrow.svg?logo=github&style=social)](https://github.com/katanaml/sparrow)")

        col1, col2, col3 = st.columns(3)
        col2.image(Image.open('assets/ab.png'))

        st.markdown("<h1 style='text-align: center; color: black; font-weight: bold;'>Andrej Baranovskij, Founder Katana ML</h1>",
                    unsafe_allow_html=True)

        st.info(
            'Sparrow is a tool for data extraction from PDFs, images, and other documents. It is a part of Katana ML, '
            'a platform for data science and machine learning.')

        icon_size = 20

        st_button('youtube', 'https://www.youtube.com/@AndrejBaranovskij', 'Andrej Baranovskij YouTube channel', icon_size)
        st_button('medium', 'https://andrejusb.medium.com', 'Read my Blogs on Medium', icon_size)
        st_button('twitter', 'https://twitter.com/andrejusb', 'Follow me on Twitter', icon_size)
        st_button('linkedin', 'https://www.linkedin.com/in/andrej-baranovskij/', 'Follow me on LinkedIn', icon_size)
        st_button('', 'https://katanaml.io', 'Katana ML', icon_size)
