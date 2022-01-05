ROS client

Description:
Demo ROS navigation on client side. We build all of source as Docker image. This client will connect to ROS master (Ohmni_bot) and revice command to excute run to the set point.

Step:
 1. Pull docker image by command "docker pull danglehoaihieu/ohmni_ros_client:ohmni_ros1.3"
 2. Run docker "sudo docker run -it ohmni_ros:1.3"
 3. Export necessary info before running any ROS tool:
	export ROS_IP=[local_machine_ip]
	export ROS_MASTER_URI=http://[bot_ip]:11311
 4. Run cmd: "roslaunch tb_navigation tb_navigation.launch"
 5. Run cmd: "python3 home/send_goal.py"
 
 Note:
 This tb_navigation contains our private map so, you can use slam method to get your map and follow below step:
  - Put your map (.pgm, .yaml) to "/home/catkin_ws/src/tb-simulation/ros_ws/src/tb_sim/tb_navigation/maps"
  - At "/home/dhp/catkin_ws/src/tb-simulation/ros_ws/src/tb_sim/tb_navigation/launch/tb_navigation.launch":
   	edit "<arg name="map_file" default="$(find tb_navigation)/maps/<name map>.yaml"

