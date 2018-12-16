ARG PYTHON_VERSION="3.6"

FROM python:$PYTHON_VERSION-alpine

ENV PYTHON_VERSION="$PYTHON_VERSION"

COPY bin /root/bin/
COPY etc /root/etc/

RUN apk --update upgrade && \
    apk add --no-cache --virtual .build-deps \
      tzdata \
      build-base \
      py-mysqldb \
      gcc \
      libc-dev \
      libffi-dev \
      mariadb-dev && \
    apk add --no-cache \
      supervisor \
      postgresql-client \
      inotify-tools && \
    apk add --no-cache --virtual postgresql-dev && \
    pip install -r "/root/etc/requirements.txt" && \
    apk add --virtual mariadb-client-libs && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    echo "Asia/Tokyo" > /etc/timezone && \
    apk del .build-deps

EXPOSE 8082/TCP

ENTRYPOINT ["/root/bin/entrypoint"]
CMD ["supervisord"]
