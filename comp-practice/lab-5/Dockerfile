FROM python:3.11-alpine

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY .. /app

EXPOSE 5000

ENTRYPOINT [ "python" ]

CMD [ "main.py" ]
