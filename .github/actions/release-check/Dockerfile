FROM python:3.10-slim

RUN pip install --no-cache-dir pydantic pygithub rtoml

WORKDIR /app

COPY main.py /app/main.py

CMD ["python", "/app/main.py"]
