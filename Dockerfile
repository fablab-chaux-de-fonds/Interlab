FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash - \
	&& apt-get install -y nodejs
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt-get update \
      && apt-get install -y \
            gettext \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
COPY manage.py /code/
COPY frontend /code/frontend/
COPY interlab /code/interlab/
WORKDIR /code/frontend
RUN npm i
RUN npm run build
RUN rm -rf /code/frontend/node_modules/
WORKDIR /code/
RUN ["/bin/bash", "-c", "SECRET_KEY=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 32 ; echo '') python manage.py collectstatic --noinput --clear"]