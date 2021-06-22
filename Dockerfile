FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash - \
	&& apt-get install -y nodejs
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/
RUN cd frontend \
	&& npm ci \
	&& npm run build
RUN python manage.py collectstatic --noinput --clear 
