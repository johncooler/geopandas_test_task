FROM python:3.9.18-bullseye 
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY ./main.py /app
LABEL version="1.0"
LABEL maintainer="johncooler"
LABEL description="Simple tool that converts Shapely Multipolygons and Points to clean Polygons"
