FROM python:3.7.4

ARG USER_ID
ARG GROUP_ID

RUN groupadd -r --gid $GROUP_ID runner; exit 0
RUN useradd -rm -d /home/runner -s /bin/bash -G sudo --uid $USER_ID --gid $GROUP_ID runner
USER runner

ENV PORT 5956

VOLUME /data

EXPOSE $PORT

ADD maven-mirror.py /opt/maven-mirror/

ENTRYPOINT [ "python3", "/opt/maven-mirror/maven-mirror.py", "/data/" ]