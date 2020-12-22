FROM centos:7.2.1511

WORKDIR /sree
COPY ["static", "/sree/static"]
COPY ["xmlparser.py", "app.py", "/sree/"]

RUN yum install -y epel-release
RUN yum install -y python2-pip
RUN pip install flask requests

ENV SREE_PORT 5000
ENV FLASK_DEBUG False
ENV S3_ENDPOINT "http://s3.amazonaws.com"
ENV S3_EXT_ENDPOINT "http://s3.amazonaws.com"
ENV S3_REGION "us-east-1"

ENTRYPOINT ["python", "/sree/app.py"]
