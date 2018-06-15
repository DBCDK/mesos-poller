FROM docker.dbc.dk/dbc-stretch:latest
MAINTAINER DBC <dbc@dbc.dk>

ENV HTTP_PORT=8888
ENV USER=""
ENV PASSWORD=""
LABEL HTTP_PORT="Port to listen for http requests on (default: 8888)"
LABEL USER="User Id for login to Mesos/Marathon"
LABEL PASSWORD="Password for login to Mesos/Marathon"


RUN useradd -u 8888 -d /var/lib/mpoller -m -s /bin/bash mpoller
RUN apt-install python3-tornado

ADD docker-entrypoint.sh /
ADD mesos-poller.py index.html /var/lib/mpoller/

USER mpoller
WORKDIR /var/lib/mpoller
EXPOSE 8888
CMD [ "/bin/bash", "-c", "/docker-entrypoint.sh" ]
