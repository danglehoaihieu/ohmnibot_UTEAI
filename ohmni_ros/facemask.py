from os import truncate
from threading import Thread
import threading
import time
import argparse
import json
import base64
import numpy

from PIL import Image
from PIL import ImageDraw, ImageFont

from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
import cv2
import socket
# lock = threading.Lock()
# warning = False


class facemask():
	def __init__(self, name):
		# super(facemask, self).__init__()
		self.name= name
		self.botshell = None
		self.FORMAT = "utf8"
		self.lock = threading.Lock()
		self.warning = False

		self.model = "./face_folder/efficientdet-lite-face4k_20ep_edgetpu.tflite"
		self.labels = "./face_folder/labels.txt"
		self.threshold = 0.5
		self.output = "./face_result/"
		self.sendImg = None

	def run(self):
		self.create_socket()

		labels = read_label_file(self.labels) if self.labels else {}
		interpreter = make_interpreter(self.model)
		interpreter.allocate_tensors()

		print("Allocate_tensors Done!")
		#img = cv2.imread('./3.png')
		#self.send_image(img)
		# define a video capture object
		vid = cv2.VideoCapture(0) # 0: cam front , 1: cam neck
		count_frame = 0
		print("Connected to camera Done!")
		while(True):
			
			ret, frame = vid.read()
			if frame is not None:
				try:
					image_cv = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
					image = Image.fromarray(image_cv)

					# image = Image.open(args.input)
					_, scale = common.set_resized_input(
					interpreter, image.size, lambda size: image.resize(size, Image.ANTIALIAS))		

					start = time.perf_counter()
					interpreter.invoke()
					inference_time = time.perf_counter() - start
					objs = detect.get_objects(interpreter, self.threshold, scale)
					fps = 1/(inference_time )
					# print('fps', fps)

					# Display the resulting frame
					if not objs:
						print( "nooo")
						image = image.convert('RGB')
						self.draw_NONobjects(ImageDraw.Draw(image), fps)
						# print('No objects detected')
						# self.set_warning(False)
					else:
						print( "detected")
						#self.botshell.sendall(("say a \n").encode(self.FORMAT))
						#fulldata =  self.handle_recv()
						# print('Number of objects: ', objs.count)
						# self.set_warning(True)
						# print("warning: ",self.warning)
						# for obj in objs:
						# 	print(('label {}:{}, score {}, ').format(obj.id, labels.get(obj.id, obj.id), obj.score))
							# print('  id:    ', obj.id)
							# print('  score: ', obj.score)
							# print('  bbox:  ', obj.bbox)

						image = image.convert('RGB')
						print( "detected1")
						self.draw_objects(ImageDraw.Draw(image), objs, labels, fps)
						print( "detected2")
						self.send_image(image)
						print( "detected3")

					#image.save(self.output + str(count_frame) + ".jpg")
					
					count_frame += 1
				except Exception as e:
					print("error: ", e)
					break
			
			
        		
		vid.release()
		cv2.destroyAllWindows()

	def draw_objects(self, draw, objs, labels, fps):
 
		for obj in objs:
			color = 'red'
			if obj.id == 0 :
				color = "green"
			bbox = obj.bbox
			draw.rectangle([(bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax)],
						outline=color)
			draw.text((bbox.xmin + 10, bbox.ymin + 10),
					'%s\n%.2f' % (labels.get(obj.id, obj.id), obj.score),
					fill=color)
			draw.text((20,20),
					str(fps),
					fill='red')

	def draw_NONobjects(self, draw, fps):
		draw.text((20,20),
					str(fps),
					fill='red')

	
	def set_warning(self, stt):
		self.lock.acquire()
		try:
			self.warning = stt
		finally:
			self.lock.release()

	def get_warning(self):
		self.lock.acquire()
		try:
			return self.warning, 
		finally:
			self.lock.release()
	
	def send_image(self, img):
		self.botshell.sendall(("say a \n").encode(self.FORMAT))
		fulldata =  self.handle_recv()
		print( "send_image")
		retval, buffer_img= cv2.imencode('.jpg', numpy.array(img))
		print( "send_image 2")
		encode = base64.b64encode(buffer_img)
		print( "send_image 3")
		data = {"name": encode}
		# data = {"name": base64.encodebytes(img).decode('utf-8')}
		# print(data)
		self.botshell.sendall(("send_to_stand_alone_api {}".format(data)).encode(self.FORMAT))
		print( "send_image 5")
		
		# retval, buffer_img = cv2.imencode('.jpg', frame)

		# resdata = base64.b64encode(buffer_img)

		# resdata = "data:image/png;base64,"+ str(resdata.decode("utf-8"))
		# PARAMS = {'image': resdata}

	def create_socket(self):
		self.botshell = None
		self.botshell = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
		self.botshell.connect("/app/bot_shell.sock")
		self.botshell.settimeout(0.01)
		print("Socket facemask created!!!")
	
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
	
if __name__ == '__main__':
	try:

		main_thread = facemask("thread facemask")

		main_thread.run()
		# while True:
		# 	pass
		
	except Exception as e:
		print("Error:", e) 
