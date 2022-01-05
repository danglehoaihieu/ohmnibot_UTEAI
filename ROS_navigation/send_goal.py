#!/usr/bin/env python3
# license removed for brevity

import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import Bool, String

def movebase_client(x, y, w):
    w = w*0.0174532925 # convert to radian
    client = actionlib.SimpleActionClient('move_base',MoveBaseAction)
    client.wait_for_server()

    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = "map"
    goal.target_pose.header.stamp = rospy.Time.now()
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    goal.target_pose.pose.orientation.w = 1.0
    goal.target_pose.pose.orientation.z = w

    client.send_goal(goal)
    wait = client.wait_for_result()
    if not wait:
        rospy.logerr("Action server not available!")
        rospy.signal_shutdown("Action server not available!")
    else:
        return client.get_result()
def decode_cmd(cmd):
	cmd = cmd.split(' ')
	x = float(cmd[0])
	y = float(cmd[1])
	w = float(cmd[2])
	return x, y, w

def gohome():
	result = False
	result = movebase_client(-0.5, 0, 0)
	if result:
		rospy.loginfo("Goal execution done!")

def goWorkspace():
	result = False
	result = movebase_client(-1, 0, 180)
	if result:
		rospy.loginfo("Goal execution done!")

def callback_bot(data):
	print("bot send: ",data.data)
	if data.data == 'gohome':
		gohome()
		print("go home and send to bot TRUE")
		pub.publish('athome')
	if data.data == 'goworkspace':
		goWorkspace()
		print("go WorkSpace and send to bot TRUE")
		pub.publish('atworkspace')


rospy.init_node('movebase_client_py')
pub = rospy.Publisher('/home', String, queue_size=1)
sub = rospy.Subscriber('/bot', String, callback_bot)	

if __name__ == '__main__':
	try:
		while True:
			pass

	except rospy.ROSInterruptException:
		rospy.loginfo("Navigation test finished.")

