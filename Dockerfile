# Ubuntu OS to run docker
FROM python:3.8.8

MAINTAINER dingxutao <dingxt@xxxx.com>

ENV PROJECT_ANME property_dp

ENV PROJECT_PATH ~/apps

RUN mkdir /$PROJECT_ANME

# When using COPY with more than one source file, the destination must be a directory and end with a /
COPY ./requirements /$PROJECT_ANME/requirements/

COPY ./config /$PROJECT_ANME/config

COPY ./config /$PROJECT_ANME/config

COPY ./$PROJECT_ANME /$PROJECT_ANME/$PROJECT_ANME

COPY ./script /$PROJECT_ANME/script

COPY property/static /$PROJECT_ANME/static

COPY property_dp_uwsgi.ini /$PROJECT_ANME/property_dp_uwsgi.ini

# -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
# -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
#RUN pip3 install -r /$PROJECT_ANME/requirements/dev.txt -i https://pypi.python.com/simple/ --trusted-host pypi.python.com
RUN pip3 install -r /$PROJECT_ANME/requirements/dev.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

RUN mkdir /logs

RUN mkdir -p /data/logs

VOLUME ["/data/logs"]

EXPOSE 8000

# Build Image:      docker build -t property:dev .
# Start Container:  docker run -p 8000:8000 -d --name property property:dev
# Go into Container: docker exec -it 213g435j bash
CMD ["uwsgi", "--ini", "/property_dp/property_dp_uwsgi.ini"]


# Some Issues, If a container run failed,then
# 1: get this container pid: docker ps -a
# 2: save temporary scene to a image:  docker commit 837ffa1d4 user/temp
# 3: run a container using  the temporary image: docker run -it user/temp bash