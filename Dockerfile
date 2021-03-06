FROM python:3.7.4-alpine3.10

ENV PYTHONUNBUFFERED 1

EXPOSE 5000

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV FLASK_APP="/code/lego/__init__.py"
ENV FLASK_DEBUG=1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

# Create database and add teams specified in teams_prod.txt
RUN chmod +x setup.sh
RUN sh setup.sh

# Run lego-app
CMD flask run --host=0.0.0.0 --port=5000 --no-debugger --with-threads --no-reload
