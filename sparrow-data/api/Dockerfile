FROM python:3.7-slim

WORKDIR /code

COPY requirements-fastapi.txt ./

RUN pip install --no-cache-dir --upgrade -r /code/requirements-fastapi.txt

RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app/

CMD ["uvicorn", "endpoints:app", "--host", "0.0.0.0", "--port", "7860"]