FROM debian:bullseye-slim

LABEL maintainer="CWO - github.com/c-w-o"
LABEL org.opencontainers.image.source=https://github.com/c-w-o/dayzserver

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update \
    && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        python3 \
        net-tools \
        nano \
        lib32stdc++6 \
        lib32gcc-s1 \
        libcurl4 \
        wget \
        ca-certificates \
    && \
    apt-get remove --purge -y \
    && \
    apt-get clean autoclean \
    && \
    apt-get autoremove -y \
    && \
    rm -rf /var/lib/apt/lists/* \
    && \
    mkdir -p /steamcmd \
    && \
    wget -qO- 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar zxf - -C /steamcmd

ENV DAYZ_BINARY=./DayZServer
ENV DAYZ_CONFIG=serverDZ.cfg
ENV DAYZ_PROFILE=main
ENV DAYZ_LIMITFPS=60
ENV PORT=3302
ENV SKIP_INSTALL=false
ENV STEAM_USER=
ENV STEAM_PASSWORD=

EXPOSE 3302/udp
EXPOSE 3303/udp
EXPOSE 3304/udp
EXPOSE 3305/udp
EXPOSE 3306/udp

WORKDIR /tmp

VOLUME /dayz
VOLUME /steamcmd
VOLUME /var/run/share/dayz/this-server

STOPSIGNAL SIGINT

COPY launch.py /

CMD ["python3","/launch.py"]
