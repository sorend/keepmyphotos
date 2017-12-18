FROM python:3.6.3-alpine3.6

RUN addgroup -g 1000 kmp && \
	adduser -D -u 1000 -G kmp kmp

ADD . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

USER kmp

ENTRYPOINT ["python3", "keepmyphotos.py"]
