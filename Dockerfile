FROM python:3.12-slim
LABEL maintainer="jpuerto@psc.edu"
LABEL org.opencontainers.image.source="https://github.com/pscedu/cpra.mp.management"

WORKDIR /usr/src/app
COPY requirements.txt

RUN mkdir -p cpra/mp/data && pip install -r requirements.txt \
    && python -m pip cache purge

COPY cpra/ ./cpra

EXPOSE 8001
CMD ["python3", "-u", "-m", "cpra.mp.management"]
