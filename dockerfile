FROM python:3.8-slim-buster

COPY module/my_azure_storage.py app/
COPY requirements.txt app/
COPY app.py app/
COPY static app/


WORKDIR /app

RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD ["python3", "app.py"]