FROM fedora:latest
MAINTAINER "Laurent Rineau" <laurent.rineau@cgal.org>

RUN yum -y update
RUN yum -y install python-pip && yum clean all

ADD LICENSE requirements.txt webhooks.py config.json hooks /src/

RUN cd /src; pip install -r requirements.txt

EXPOSE 5000

WORKDIR /src
CMD ["python", "/src/webhooks.py"]
