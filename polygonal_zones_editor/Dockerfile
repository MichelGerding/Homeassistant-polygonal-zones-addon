ARG BUILD_FROM
FROM $BUILD_FROM

RUN \
  apk add --no-cache \
    python3 \
    py3-pip

# install dependencies
RUN \
   apk add --no-cache \
    py3-starlette \
    uvicorn

WORKDIR /app

COPY app /app
EXPOSE 8000

COPY app/static/zones.json /data/polygonal_zones/zones.json

WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
