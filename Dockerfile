FROM python:3
ENV PYTHONUNBUFFERED=1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Install dependencies
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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Copy content
COPY manage.py /code/
COPY frontend /code/frontend/
COPY interlab /code/interlab/
COPY accounts /code/accounts/
COPY newsletter /code/newsletter/
COPY user_profile /code/user_profile/
COPY locale /code/locale/

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# Front-end generation
WORKDIR /code/frontend

# Install dependencies from package-lock file
RUN npm ci
RUN npm run build
RUN rm -rf /code/frontend/node_modules/

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Final steps
WORKDIR /code/

# Static files collection
RUN ["/bin/bash", "-c", "SECRET_KEY=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 32 ; echo '') python manage.py collectstatic --noinput --clear"]

# Translation collection
RUN django-admin makemessages -l fr -e html,txt --ignore 'build/*' --ignore 'frontend/*'

# Prepare LC translation binary file
RUN django-admin compilemessages