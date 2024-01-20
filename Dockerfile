FROM python:3.11

WORKDIR /usr/src/app
 
ENV PYTHONDONTWRITEBYTECODE 1
 
ENV PYTHONUNBUFFERED 1

RUN pip3 install --upgrade pip setuptools

RUN apt-get update \
    && apt-get install -y libproj-dev proj-data proj-bin dos2unix libeccodes-dev libeccodes0

RUN pip3 install cartopy

RUN pip3 install matplotlib
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN dos2unix /usr/src/app/entrypoint.sh && apt-get --purge remove -y dos2unix
RUN chmod +x /usr/src/app/entrypoint.sh

COPY . /usr/src/app
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
