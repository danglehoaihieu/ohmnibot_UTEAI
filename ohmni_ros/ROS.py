from threading import Thread
import time
 


class ROS(Thread):
	def __init__(self, name):
		super(ROS, self).__init__()
		self.name= name
		self.botshell = None
		self.FORMAT = "utf8"

	def run(self):
		print ("Start: " + self.name)
		while True:
			print( "%s", time.ctime(time.time()))
			time.sleep(200)





