FROM python:3.8.9

WORKDIR /usr/src/sparrow

RUN apt-get update
RUN apt-get install -y tesseract-ocr

COPY requirements.txt ./

RUN pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

RUN pip install torch==1.10.0+cu111 torchvision==0.11.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html

COPY setup.py ./

RUN python setup.py