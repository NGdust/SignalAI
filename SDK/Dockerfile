FROM python:3.8

RUN apt-get update  &&  apt-get install alsa-utils libgl1 libpulse-mainloop-glib0 gcc-4.9 lib32stdc++6 qt5-default -y
RUN apt-get upgrade libstdc++6 -y


RUN mkdir /SKD
WORKDIR ./SDK
COPY . /SDK
RUN cp ./lib/* /lib/x86_64-linux-gnu/
RUN cp ./lib/* /usr/lib/x86_64-linux-gnu/
#RUN wget https://firebasestorage.googleapis.com/v0/b/my-files-for-projects.appspot.com/o/husen%2FEPU_III_SDK_3D-3.6.7.0-Ubuntu-Silent-For-Distrib.tar.xz?alt=media&token=00facd77-2e99-43d4-b25b-f88d446d42d7
RUN tar -xf EPU_III_SDK_3D-3.6.7.0-Ubuntu-Silent-For-Distrib.tar.xz