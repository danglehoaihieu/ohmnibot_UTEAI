# Ohmni_UTEAI
This is a project implemented on Robot OhmniBot, which is a product of ohmnilab company. The project is oriented on developing self-driving applications in universities with some functions such as reception, fmask detection, autodock.
## Environment
All source code were packaged as the docker image that you can pull and run on top of Ohmni OS.
Here are the steps to up and running.
### Step 1: Pull the docker to bot
In bot: docker pull danglehoaihieu/ohmni_ros_bot:2.11
### Step 2: Run docker

Copy ohmni_ros folder to path /var/ in Ohmni OS

In bot: docker run -it --network host -v /var/ohmni_ros/tb_control:/opt/ros/melodic/share/tb_control  -v /var/ohmni_ros:/home/ohmnidev -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data --privileged -v /dev:/dev -e ROS_IP=192.168.1.5 ohmni_ros:2.11

For brevity, the command above is run using a SH file at the path /system/bin/ohmni_ros. you can copy this file in folder A above

