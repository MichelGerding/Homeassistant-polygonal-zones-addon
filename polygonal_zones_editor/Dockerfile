ARG BUILD_FROM
#FROM $BUILD_FROM
FROM alpine:latest

RUN \
    apk update && apk upgrade

RUN \
  apk add --no-cache \
    python3 \
    py3-pip

# setup env so we can install requirements using pip instead of apk.
# uvicorn is not available in the homeassistant alpine image.
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip3 install --upgrade pip
# install dependencies

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

COPY app /app
EXPOSE 8000

COPY app/static/zones.json /data/polygonal_zones/zones.json

WORKDIR /app
CMD ["python", "main.py"]
