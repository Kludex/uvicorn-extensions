FROM python:3.10-slim

RUN pip install --no-cache-dir pydantic pygithub

WORKDIR /app

COPY main.py /app/main.py

CMD ["python", "/app/main.py"]
