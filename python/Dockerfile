FROM python:3.12.2
RUN apt-get update && apt-get install -y graphviz libgraphviz-dev
WORKDIR /usr/src/app
COPY pyproject.toml .
RUN python3 -m pip install --upgrade pip && python3 -m pip install .[dev]
