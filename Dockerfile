FROM python:3.7.4-alpine3.10

ENV PYTHONUNBUFFERED 1
ENV http_proxy 'http://16.46.41.11:8080'
ENV https_proxy 'http://16.46.41.11:8080'
ENV no_proxy '*.uk.rdlabs.hpecorp.net,localhost,127.0.0.1,0.0.0.0'

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV FLASK_APP="/code/lego/__init__.py"
ENV FLASK_DEBUG=1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

# RUN /bin/bash -c "flask init" - does not work as can't do input in build
# RUN flask add-teams /code/teams_example.txt - would work but database won't exist until init is run

CMD flask run --host=0.0.0.0 --port=5000 --no-debugger --with-threads --no-reload