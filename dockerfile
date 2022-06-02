FROM python:3.8-slim-buster

COPY module/my_azure_storage.py /app/my_azure_storage.py
COPY requirements.txt /app/requirements.txt
COPY app.py /app/app.py

WORKDIR /app

RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD ["python3", "app.py"]