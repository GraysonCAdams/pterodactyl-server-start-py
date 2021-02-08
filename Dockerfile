# pull official base image
FROM python:3.7 as base

ENV DEBIAN_FRONTEND noninteractive

# update base image
RUN apt-get update \
  && apt-get upgrade -y \
  && pip3 install --upgrade pip

# set work directory
WORKDIR /usr/src/app

# set environment variables
# Prevents Python from writing pyc files to dis
ENV PYTHONDONTWRITEBYTECODE 1m
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# copy project
ADD . /usr/src/app/
ADD requirements.txt /usr/src/app/requirements.txt

# install dependencies
RUN pip3 install -r requirements.txt

ENV DEBIAN_FRONTEND teletype