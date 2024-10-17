FROM python:3.10

RUN useradd -m -u 1000 user
WORKDIR /app

COPY --chown=user ./requirements_sparrow_parse.txt requirements_sparrow_parse.txt
RUN pip install --no-cache-dir --upgrade -r requirements_sparrow_parse.txt

COPY --chown=user . /app
CMD ["python", "api.py", "--port", "7860"]