FROM python:3.11-slim

WORKDIR /sparrow/sparrow-ui

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

CMD ["streamlit", "run", "main.py", "--server.port=7860", "--server.address=0.0.0.0"]