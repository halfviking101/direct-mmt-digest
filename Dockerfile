# syntax=docker/dockerfile:1

FROM python:alpine3.18@sha256:116ccee352c283c40a75e636b6ea3decffd9ec6c39fbf2022128595483d1a6f6

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
