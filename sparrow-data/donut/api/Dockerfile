FROM python:3.10

WORKDIR /code

COPY requirements-fastapi.txt ./

# Installing libGL
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev

RUN apt-get install -y poppler-utils libpoppler-cpp-dev

RUN pip install --no-cache-dir --upgrade -r /code/requirements-fastapi.txt

COPY set_env_vars.sh /set_env_vars.sh
COPY start.sh /start.sh

# Make the scripts executable
RUN chmod +x /set_env_vars.sh /start.sh

RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app/

CMD ["/start.sh"]