FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /main
WORKDIR /main
COPY . /main
COPY requirements.txt /main
RUN pip install -r requirements.txt