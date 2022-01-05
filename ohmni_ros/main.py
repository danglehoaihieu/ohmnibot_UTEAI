import argparse
from logging import fatal
from pickle import TRUE
import platform
import subprocess

import socket
import os, os.path
import sys
from enum import Enum
from struct import *
from threading import Thread
import time
from ROS import ROSThread
import rospy
from std_msgs.msg import Bool, String
# from facemask import facemask

rospy.init_node('bot_ros', anonymous=True)

class mainThread(Thread):
	def __init__(self, name):
		super(mainThread, self).__init__()
		self.name= name
		self.botshell = None
		self.FORMAT = "utf8"
		self.homePoint = rospy.Subscriber("/home", String,self.callback_homePoint, queue_size = 1)
		self.gohome = rospy.Publisher("/bot", String, queue_size=1)
		self.atHome = False
		self.start_time = time.time()
		self.ROS_running = False

	def callback_homePoint(self, data):
		print('self.autodock: ', data.data)
		if data.data == 'athome':
			self.autodock_api()
			self.ROS_running = False
		else:
			self.ROS_running = False


	def run(self):
		count = 0
		print ("Start: " + self.name)
		self.create_socket()
		fulldata = self.handle_recv()
		# self.set_workspace()
		while True:
			try:
				# if self.timeToCheckBattery() and not self.ROS_running : 
				# 	self.check_batery()
				print("please input cmd: ")
				x = input()
				# warning = facemask_thread.get_warning()
				# print("thread1 warning: ", warning)

				# print("thread1 warning: ", warning)
				# x = "a"
				if x == "out":
					print("stop : " +  self.name)
					self.botshell.close()
					break
				elif x == "off" :
					self.turnOffSerial()
				elif x == "on":
					self.turnOnSerrial()
				elif x == "home": #self.check_batery()
					self.set_gohome()
				elif x == "ws": #self.check_batery()
					self.set_workspace()
				
				# elif warning:
				# 	# print ("face mask")
				# 	self.botshell.sendall(("say a\n").encode(self.FORMAT))
				# 	fulldata = self.handle_recv()
				else:
					self.botshell.sendall((x+"\n").encode(self.FORMAT))
					fulldata =  self.handle_recv()
					print("recv: ", fulldata)
					
					
			except:
				print ("RETRY socket")
				self.create_socket()

	def create_socket(self):
		self.botshell = None
		self.botshell = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
		self.botshell.connect("/app/bot_shell.sock")
		self.botshell.settimeout(0.01)
		print("Socket created!!!")

	def handle_recv(self):
		fulldata = ""
		while True:		
			try:
				data = self.botshell.recv(4096).decode(self.FORMAT)
				fulldata += data
			except socket.timeout as e:
				# print("socket timeout")
				break
		return fulldata

	def turnOffSerial(self):
		# self.botshell.sendall(("say off serial\n").encode(self.FORMAT))
		# fulldata =  self.handle_recv()
		self.botshell.sendall(("light_color 20 160 255 255\n").encode(self.FORMAT)) # blue light
		fulldata = self.handle_recv()
		self.botshell.sendall(("serial off\n").encode(self.FORMAT))
		fulldata = self.handle_recv()
		

	def turnOnSerrial(self):
		self.botshell.sendall(("serial on\n").encode(self.FORMAT))
		print("waiting to serial on...")
		time.sleep(5)
		self.create_socket()
		fulldata = self.handle_recv()
		# self.botshell.sendall(("say turn on serial\n").encode(self.FORMAT))
		# fulldata =  self.handle_recv()
		self.botshell.sendall(("light_color 20 43 255 255\n").encode(self.FORMAT)) # red light
		fulldata = self.handle_recv()

	def check_batery(self):
		self.turnOnSerrial()
		self.botshell.sendall(("battery\n").encode(self.FORMAT))
		fulldata =  self.handle_recv()
		bat_value, dock_stt = self.handleBatteryInfo(fulldata)
		self.turnOffSerial()

		if bat_value < 4000 and dock_stt == "0": # battery < 20% and NO docking => goto home
			self.set_gohome()
		elif bat_value > 4000 and dock_stt == "1": # battery > 80% and docking => goto workspace
			self.set_workspace()


	def handleBatteryInfo(self, data):
		parse_data = data.split()
		print("battery_data: ",parse_data)
		bat_value = 0
		for i in range(3,8):
			bat_value += int(parse_data[i].replace(',',''))
		bat_value /= 5
		print("total: ",bat_value)
		return bat_value, parse_data[11]
	
	def set_gohome(self):
		print("set gohome")
		self.ROS_running = True
		self.gohome.publish('gohome')

	def set_workspace(self):
		print("set go workSpace")
		self.ROS_running = True
		self.gohome.publish('goworkspace')

	def autodock_api(self):
		self.turnOnSerrial()
		fulldata =  self.handle_recv()
		self.botshell.sendall(("autodock\n").encode(self.FORMAT))
		dock_complete = self.autodockHandle()
		# if not dock_complete: #retry if failed
		# 	self.botshell.sendall(("autodock\n").encode(self.FORMAT))
		# 	dock_complete = self.autodockHandle()
		self.turnOffSerial()

	def autodockHandle(self):
		autodoc_t1 = time.time()
		print('start autodock')
		while int(time.time() - autodoc_t1) < 120: #waiting to recive data in 2 minute
			fulldata =  self.handle_recv()
			print("autock send: ",fulldata, int(time.time() - autodoc_t1))
			if 'done' in fulldata:
				if self.check_docked:
					print("autodock = TRUE")
					return True
				print("autodock = FALSE")
				return False

		return False

	def check_docked(self): #using when serial ON
		self.botshell.sendall(("battery\n").encode(self.FORMAT))
		fulldata =  self.handle_recv()
		bat_value, dock_stt = self.handleBatteryInfo(fulldata)
		if dock_stt == '1':
			return True
		else:
			return False


	def timeToCheckBattery(self):
		timelapse = int(time.time() - self.start_time)
		if timelapse%20 == 0: #20s
			return True
		else:
			return False

try:
	# sub = rospy.Subscriber("/home", Bool, callback_homePoint2, queue_size = 1)
	main_thread = mainThread("thread 1")
	# facemask_thread = facemask("thread 2")
	# facemask_thread.start()
	main_thread.start()
	# while True:
	# 	pass
	
except:
	print("Error") 
 





