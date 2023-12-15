FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

COPY --chown=user config/config.toml $HOME/app/.streamlit/config.toml

CMD ["streamlit", "run", "main.py", "--server.port=7860", "--server.address=0.0.0.0"]
