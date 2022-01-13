FROM python:3.8.9

WORKDIR /usr/src/sparrow

RUN apt-get update
RUN apt-get install -y tesseract-ocr

COPY requirements.txt ./

RUN pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

RUN pip install torch==1.8.0+cu101 torchvision==0.9.0+cu101 -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install -q detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu101/torch1.8/index.html

COPY setup.py ./

RUN python setup.py