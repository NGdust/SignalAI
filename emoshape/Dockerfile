FROM python:3.8

ENV PYTHONUNBUFFERED 1
#
#RUN pactl load-module module-pipe-source source_name=virtmic file=/emoshape/virtmic format=s16le rate=16000 channels=1
#RUN pactl set-default-source virtmic

RUN mkdir /emoshape
WORKDIR /emoshape
COPY . /emoshape
COPY requirements.txt /emoshape
RUN pip install -r requirements.txt