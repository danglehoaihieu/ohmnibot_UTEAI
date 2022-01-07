# Ohmni_UTEAI
This is a project implemented on Robot OhmniBot, which is a product of ohmnilab company. The project is oriented on developing self-driving applications in universities with some functions such as reception, facemask detection, autodock.
## Environment
All source code were packaged as the docker image that you can pull and run on top of Ohmni OS.
Here are the steps to up and running.
### Step 1: Pull the docker to the bot
In bot: docker pull danglehoaihieu/ohmni_ros_bot:2.11
### Step 2: Run docker
Copy ohmni_ros folder to path /var/ in Ohmni OS.

In bot: docker run -it --network host -v /var/ohmni_ros/tb_control:/opt/ros/melodic/share/tb_control  -v /var/ohmni_ros:/home/ohmnidev -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data --privileged -v /dev:/dev -e ROS_IP=192.168.1.5 ohmni_ros:2.11

For brevity, the command above is run by using a SH file at the path /system/bin/ohmni_ros_env. You can copy ohmni_ros_env file above to that path.
## Making a map for the bot
A map needs to be made before the bot works. You can use SLAM package available in docker environment with following steps
### Step 1: Launch ROS SLAM on the bot
In docker env: roslaunch tb_slam tb_slam.launch slam_methods:=hector
### Step 2: Connect the bot with the local machine
1. Export bot and local machine ip address to ROS <br />
In the local machine: export ROS_IP=[local_machine_ip] <br />
In the local machine: export ROS_MASTER_URI=http://[bot_ip]:11311
2. Use rqt_robot_steering tool to manual control the bot <br />
In the local machine: sudo apt install ros-melodic-rqt-robot-steering <br />
In the local machine: rosrun rqt_robot_steering rqt_robot_steering
### Step 3: Save the map to file
After SLAM, the map which is built can be saved as a file with the following command:

rosrun map_server map_saver -f /path to file

Put map files (.pgm, .yaml) to "/var/ohmni_ros/maps/" in Ohmni OS
## Running apps
This program is divided into several processing threads to perform communication tasks with ROS, facemask detection, and web interface interaction.
### Step 1: Launch ROS Navigation on the bot
In docker env: roslaunch tb_navigation tb_navigation.launch
### Step 2: Run main program
1. Open another terminal of the current container <br/>
docker exec -it <container> bash
2. Setup enviroment <br/>
In docker env: source /opt/ros/melodic/setup.bash <br/>
In docker env: source /home/hieu/catkin_ws/devel/setup.bash <br/>
3. Run main program at path /home/ohmnidev/ <br/>
In docker env: python3 main.py
### Step 3: (optional) Connect the bot with the local machine
The local machine could to be use to ROS debug and visualize the map






