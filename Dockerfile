FROM alpine
MAINTAINER carlos.novo.negrillo@gmail.com	

RUN apk add python3 \
        py3-pip \
        bash \
        vim

RUN pip3 install tinytuya prometheus_client pyyaml simplejson pickledb

CMD tail -f /dev/null
