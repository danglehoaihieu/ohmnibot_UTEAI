import argparse
import platform
import subprocess

import socket
import os, os.path
import sys
from enum import Enum
from struct import *

# Open connection to bot shell and send some commands
def create_socket():
	global botshell
	botshell = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
	botshell.connect("/app/bot_shell.sock")
	botshell.settimeout(0.2)
	

def handle_recv():
	fulldata = ""
	while True:		
		try:
			data = botshell.recv(4096).decode(FORMAT)
			fulldata += data
		except socket.timeout as e:
			print("socket timeout")
			break
	return fulldata

# def turnoffSerial():
# 	create_socket()
# 	botshell.sendall(("offserial off\n").encode(FORMAT))
# 	fulldata = handle_recv()
# 	print("offserail: ",fulldata)
# 	botshell.sendall(("say turn off serial\n").encode(FORMAT))
# 	fulldata = handle_recv()
# 	print("say: ",fulldata)
# 	botshell.sendall(("light_color 20 120 100 100\n").encode(FORMAT)) # blue light
# 	fulldata = handle_recv()
# 	print("set light color: ",fulldata)
# 	botshell.close()
	
def turnoffSerial():
	create_socket()
	botshell.sendall(("light_color 20 160 255 255\n").encode(FORMAT)) # blue light
	fulldata = handle_recv()
	print("set light color: ",fulldata)
	botshell.sendall(("serial off\n").encode(FORMAT))
	fulldata = handle_recv()
	print("offserail: ",fulldata)
	botshell.sendall(("say turn off serial\n").encode(FORMAT))
	botshell.close()


botshell = None
FORMAT = "utf8"
if __name__ == "__main__":
	try:	
		turnoffSerial()		
	except:
		turnoffSerial()


	


        





