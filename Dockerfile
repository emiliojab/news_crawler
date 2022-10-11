FROM python:3.10-bullseye

# create directory for the app user
RUN mkdir -p /home/app

# create the app user and the app group
RUN addgroup --system app && adduser --system app --ingroup app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/news_crawler
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/logs
WORKDIR $APP_HOME

#set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# to use nohup to run scrapyrt in the background in 
# order to be able to run scrapyrt and gunicorn from
# the entrypoint file
RUN apt-get install -y coreutils

#install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy composer-entrypoint.sh and using sed to apply
# basic text transformation to the mentioned file
# Here we are removing the \r
# Then we make the file exectutable
COPY ./composer-entrypoint.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/composer-entrypoint.sh
RUN chmod +x  $APP_HOME/composer-entrypoint.sh

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# run composer-entrypoint.sh
ENTRYPOINT ["/home/app/news_crawler/composer-entrypoint.sh"]