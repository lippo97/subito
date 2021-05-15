from python:3

WORKDIR /usr/src/app

COPY Pipfile.lock .
COPY Pipfile .

RUN pip install --system --deploy --ignore-pipfile

COPY *.py .

CMD ["python", "./main.py"]