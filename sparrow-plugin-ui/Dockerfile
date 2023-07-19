FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY set_env_vars.sh /set_env_vars.sh
COPY start.sh /start.sh

# Make the scripts executable
RUN chmod +x /set_env_vars.sh /start.sh

RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

COPY --chown=user config/config.toml $HOME/app/.streamlit/config.toml

CMD ["/start.sh"]