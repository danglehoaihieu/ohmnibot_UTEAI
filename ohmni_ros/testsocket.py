import argparse
import platform
import subprocess

import socket
import os, os.path
import sys
from enum import Enum
from struct import *
from threading import Thread
import time

#from thread2 import thread2


class mainThread(Thread):
	def __init__(self, name):
		super(mainThread, self).__init__()
		self.name= name
		self.botshell = None
		self.FORMAT = "utf8"

	def run(self):
		print ("Start: " + self.name)
		self.create_socket()
		fulldata = self.handle_recv()
		while True:
			try:
				print("please input cmd: ")
				x = input()
				if x == "out":
					print("stop : " +  self.name)
					self.botshell.close()
					break
				elif x == "off" :
					self.turnOffSerial()
				elif x == "on":

					self.turnOnSerrial()
				else:
					self.botshell.sendall((x+"\n").encode(self.FORMAT))
					fulldata = self.handle_recv()	
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
				print("socket timeout")
				break
		return fulldata

	def turnOffSerial(self):
		self.botshell.sendall(("serial on\n").encode(self.FORMAT))
		fulldata =  self.handle_recv()
		print("say: ",fulldata)
		self.botshell.sendall(("light_color 20 160 255 255\n").encode(self.FORMAT)) # blue light
		fulldata = self.handle_recv()
		print("set light color: ",fulldata)
		self.botshell.sendall(("serial off\n").encode(self.FORMAT))
		fulldata = self.handle_recv()
		print("offserail: ",fulldata)
		self.botshell.sendall(("say turn off serial\n").encode(self.FORMAT))
		

	def turnOnSerrial(self):
		print("TURN ON")
		self.botshell.sendall(("serial on\n").encode(self.FORMAT))
		print("waiting to serial on...")
		time.sleep(5)
		self.create_socket()
		fulldata = self.handle_recv()
		print("offserail: ",fulldata)
		self.botshell.sendall(("say turn on serial\n").encode(self.FORMAT))
		fulldata =  self.handle_recv()
		print("say: ",fulldata)
		self.botshell.sendall(("light_color 20 43 255 255\n").encode(self.FORMAT)) # red light
		fulldata = self.handle_recv()
		print("set light color: ",fulldata)


try:
	thread1 = mainThread("thread 1")
	#thread22 = thread2("thread 2")
	thread1.start()
	#thread22.start()
except:
	print("Error") 
 





