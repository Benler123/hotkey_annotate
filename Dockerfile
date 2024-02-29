# This Dockerfile is used to build an headles vnc image based on Debian
FROM consol/debian-xfce-vnc
COPY requirements.txt /tmp/requirements.txt

ENV REFRESHED_AT 2023-06-14

# Switch to root user to install additional software
USER 0

# Install vlc
RUN apt-get update && apt-get install -y vlc python3-pip
RUN python3 -m pip install -r /tmp/requirements.txt

# Switch back to default user
USER 1000