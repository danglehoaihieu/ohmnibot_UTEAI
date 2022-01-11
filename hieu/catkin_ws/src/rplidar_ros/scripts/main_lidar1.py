#!/usr/bin/env python3
import rospy
import cv2
import numpy as np
import time
from std_msgs.msg import String, Float32, Int32, Float32MultiArray, Bool
import sensor_msgs.msg
from geometry_msgs.msg import Twist
from itertools import *
import sys
import config as cf
import rospkg 
import threading
from operator import itemgetter
from tracker import Tracker

import imutils
import math
de2ra = 0.0174533
time_fps = time.time()
cf.out = cv2.VideoWriter('output_02.avi', cv2.VideoWriter_fourcc(*'XVID'), 30, (300, 340))
point_tracker = Tracker()

class lidar_pro:
	def __init__(self):
		self.data_lidar = np.zeros(shape=[2, 360], dtype = np.float)
		self.image_draw = np.zeros((340, 300, 3), np.uint8)
		self.img_rec = np.zeros_like(self.image_draw)
		self.image_draw2 = np.zeros((280, 460, 3), np.uint8)
		self.carX = 80#240#60
		self.carY = 300#500#100
		self.angle_min = 170#100 # >0
		self.angle_max = -170#-100 # <0
		self.scale = 100
		self.clear_all()
		
		self.sub_lidar_data = rospy.Subscriber("/scan",sensor_msgs.msg.LaserScan,self.callback_lidar, queue_size = 1)
		self.sub_rate_speed = rospy.Subscriber("/ercen", Float32, self.callback_error_center, queue_size=1)
		self.sub_bt = rospy.Subscriber("/bt4_status", Bool, self.get_bt4_status, queue_size=1)
		
	def clear_all(self):
		self.btrai = 0.15
		self.bsau = 0.3
		self.hmax= 3.0
		self.hmin = 1.2
		self.wmax = 2.0
		self.wmin = 0.3
		self.hwcar = self.scale*0.2
		self.bxa_cr = 1.5
		self.btrai_cr = 0.8
		self.bphai_cr = 0.5
		self.trans = 50
		self.bxa = self.wmax
		self.bphai = self.wmin
		self.box_obs = None
		self.start_track = False
		self.yes_obstacle = 0
		self.array = None
		self.error_center = 0.0
		self.allow_over = False
		self.allow_cross = False
		self.catched = False
		self.disappear = False
		self.bt4_old = False
		self.time_wait = time.time()
		self.start_wait = False
		self.move = 0
		self.px_array_1 = []
		self.px_array_2 = [0,0]
		self.dir_array = []
		self.count_prl = 0
		self.count_prr = 0
		self.direction = 'none'
		self.count_none = 0
	
	def get_bt4_status(self, data):
		if data.data and not self.bt4_old:
			self.clear_all()
		self.bt4_old = data.data
		time.sleep(0.1)
		
	def talker(self, data):
	  	pub1 = rospy.Publisher('/obstacle', Int32, queue_size=1)
	  	rate = rospy.Rate(10000)
	  	if (~rospy.is_shutdown()):
	  		pub1.publish(data)
	  		rate.sleep()
	  		
	def fix_roi(self):
		if self.yes_obstacle == 0:
			self.bxa = abs(self.error_center)/160*(self.hmin-self.hmax)+self.hmax
			self.bphai = abs(self.error_center)/160*(self.wmax-self.wmin)+self.wmin
		else:
			self.bxa = (self.carY - self.box_obs[1]-0.3)/self.scale
			self.bphai = abs(self.box_obs[0]+self.box_obs[2]+0.5-self.carX)/self.scale
			
		if self.bxa > self.hmax: self.bxa = self.hmax
		if self.bxa < 0: self.bxa = 0
		if self.bphai > self.wmax: self.bphai = self.wmax
		
	def tracking(self):
		if self.box_obs is None:	return 0
		x,y,w,h = self.box_obs
		w_roi = int((self.bphai+self.btrai)*self.scale)
		h_roi = int((self.bxa+self.bsau)*self.scale)
		dx = self.carX-x
		dy = self.carY-y-h
		min_dis = int(math.sqrt(dx*dx+dy*dy))
		#print('dis  h  hroi:   ', min_dis, h, h_roi,  self.start_track)
		if not self.start_track and min_dis < 45 and h > h_roi:
			self.start_track = True
		if not self.catched and self.start_track and self.yes_obstacle == 0:
				self.catched = True

	def predict_direction(self,px,wb):
		self.px_array_1.append(px)
		if len(self.px_array_1) >= 10:
			mean = np.sum(self.px_array_1)/10
			self.px_array_2[1] = mean
			if self.px_array_2[1] - self.px_array_2[0] > 1:
				self.count_prr += 1
				self.count_prl = 0
				if self.count_prr >= 5:
					print("++++++++++++++++++")
					self.direction = 'right'
					self.count_prr = 0
					self.count_none = 0
			elif self.px_array_2[1] - self.px_array_2[0] < -1:
				self.count_prl += 1
				self.count_prr = 0
				if self.count_prl >= 5:
					print("------------------")
					self.direction = 'left'
					self.count_prl = 0
					self.count_none = 0
			else:	
				self.count_prl = 0
				self.count_prr = 0
				self.direction = 'none'
				if (mean-wb/2 > self.carX+self.trans+25) or (mean+wb/2 < self.carX+self.trans-25): 
					self.count_none += 1
					print('none', self.count_none)
				print(" ")
			self.px_array_2[0] = self.px_array_2[1]
			self.px_array_1 = []
			
	def wait(self,t=1.5):
		stop = False
		#print(time.time()-self.time_wait)
		if self.start_wait:
			self.time_wait = time.time()
			self.start_wait = False
		elif time.time()-self.time_wait > t:
			stop = True
		return stop
		
	def draw_map_cross(self):
		global de2ra
		
		angle_min = self.angle_min
		angle_max = self.angle_max
		scale = self.scale
		image = np.zeros((self.image_draw.shape[0], self.image_draw.shape[1]), np.uint8)
		image_r = np.zeros_like(self.image_draw)
		img = np.zeros((self.image_draw2.shape[0], self.image_draw2.shape[1]), np.uint8)
		dist = self.data_lidar
		
		d = 0.2
		phai = int(self.bphai_cr*self.scale)
		trai = int(self.btrai_cr*self.scale)
		xa = int(self.bxa_cr*self.scale)
		dd = int(d*self.scale)
		x1 = self.carX-trai+self.trans
		y1 = self.carY-xa-dd
		x2 = self.carX+phai+self.trans
		y2 = self.carY-dd
		for i in range(angle_min, angle_max, -1):
			x = 0
			y = 0				
			if dist[0][i] < 100:
				x = int(self.carX+self.trans - scale*dist[0][i]*math.sin(dist[1][i]*de2ra))
				y = int(self.carY - scale*dist[0][i]*math.cos(dist[1][i]*de2ra))
				if x1 <= x <= x2 and y1 <= y <= y2:
					cv2.circle(image, (x, y), 6, (255, 255, 255), -1)
		contours,_ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
		bb=[]
		count_con = 0		
		
		for cnt in contours:
			x,y,w,h = cv2.boundingRect(cnt)
			a=cv2.contourArea(cnt)
			if a > 100:
				bb.append([x,y,w,h])
				count_con += 1		
		self.yes_obstacle = 1 if count_con >0 else 0
		if self.yes_obstacle == 0:
			stop = self.wait(4.0)
			if stop:
				self.move = 1
		if self.yes_obstacle > 0:
			def rey(a):
				return a[2]		
			self.box_obs = max(bb, key=rey)
			xb = self.box_obs[0]
			yb = self.box_obs[1]
			wb = self.box_obs[2]
			hb = self.box_obs[3]
			posi = [int(xb+wb/2), int(yb+hb/2)]
			posi = point_tracker.add(posi)
			#if self.direction == 'none':
			self.predict_direction(posi[0],wb)
			if self.count_none > 10:
				self.move = 1
				return 0
			#(mean-wb/2 > self.carX+self.trans+25) or (mean+wb/2 < self.carX+self.trans-25): 
			elif (self.direction=='right'and posi[0]>x2-10)or(self.direction=='left'and posi[0]>x1+10):
				self.move = 1
				return 0
			else:
				self.start_wait = True
			
			#cv2.circle(image, (posi[0], posi[1]), 3, (0,0,0), -1)
			#cv2.rectangle(image, (xb, yb), (xb+wb, yb+hb), (255, 255, 255), 2)
					
		#cv2.line(image, (x1, y2), (x1, y1), (255,255,255), 1)
		#cv2.line(image, (x1, y1), (x2, y1), (255,255,255), 1)
		#cv2.line(image, (x2, y1), (x2, y2), (255,255,255), 1)
		#cv2.line(image, (x2, y2), (x1, y2), (255,255,255), 1)
		#cv2.circle(image, (self.carX+self.trans, self.carY) ,3, (255,255,255), 3)
		
		#self.image_draw[np.where(image[:]>10)] = [255,255,255]
		#self.image_draw[np.where(image[:]<10)] = [0,0,0]
					
	def draw_map_over(self):
		global de2ra
	
		if self.catched:
			self.yes_obstacle = 0
			return 0
		
		angle_min = self.angle_min
		angle_max = self.angle_max
		scale = self.scale
		image = np.zeros((self.image_draw.shape[0], self.image_draw.shape[1]), np.uint8)
		image_r = np.zeros_like(self.image_draw)
		img = np.zeros((self.image_draw2.shape[0], self.image_draw2.shape[1]), np.uint8)
		dist = self.data_lidar
		
		phai = int(self.bphai*self.scale)
		trai = int(self.btrai*self.scale)
		xa = int(self.bxa*self.scale)
		sau = int(self.bsau*self.scale)
		x1 = self.carX-trai
		y1 = self.carY-xa
		x2 = self.carX+phai
		y2 = self.carY+sau
		for i in range(angle_min, angle_max, -1):
			x = 0
			y = 0				
			if dist[0][i] < 100:
				x = int(self.carX - scale*dist[0][i]*math.sin(dist[1][i]*de2ra))
				y = int(self.carY - scale*dist[0][i]*math.cos(dist[1][i]*de2ra))
				#cv2.circle(image, (x, y), 5, (255, 255, 255), -1)
				if x1 <= x <= x2 and y1 <= y <= y2:
					cv2.circle(image, (x, y), 4, (255, 255, 255), -1)
		#if count < 5:
		#	self.yes_obstacle = 0
		#	return 0
		# cut ROI

		mask_roi2 = np.ones((image.shape[0], image.shape[1]), np.uint8)*255 
		roi2=np.array([[(self.carX-20,self.carY+25),(self.carX-20,self.carY),(self.carX+20,self.carY),(self.carX+20,self.carY+25)]],dtype=np.int32)
		mask_roi2 = cv2.fillPoly(mask_roi2, roi2, (0, 0, 0))
		image = cv2.bitwise_and(image, mask_roi2)
		
		contours,_ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
		bb=[]
		count_con = 0
		
		#cv2.line(image, (x1, y2), (x1, y1), (255,255,255), 1)
		#cv2.line(image, (x1, y1), (x2, y1), (255,255,255), 1)
		#cv2.line(image, (x2, y1), (x2, y2), (255,255,255), 1)
		#cv2.line(image, (x2, y2), (x1, y2), (255,255,255), 1)
		
		
		for cnt in contours:
			x,y,w,h = cv2.boundingRect(cnt)
			a=cv2.contourArea(cnt)
			if a > 200:
				bb.append([x,y,w,h])
				count_con += 1		
		self.yes_obstacle = 1 if count_con >0 else 0
		if len(bb) > 0:
			def rey(a):
				return a[1]		
			self.box_obs = max(bb, key=rey)
			xb = self.box_obs[0]
			yb = self.box_obs[1]
			wb = self.box_obs[2]
			hb = self.box_obs[3]
			#cv2.rectangle(image, (xb, yb), (xb+wb, yb+hb), (255, 255, 255), 2)
		
		#self.image_draw[np.where(image[:]>10)] = [255,255,255]
		#self.image_draw[np.where(imagprinte[:]<10)] = [0,0,0]
	def over_pro(self):
		self.draw_map_over()
		self.fix_roi()
		self.tracking()
		self.talker(self.yes_obstacle)
	def cross_pro(self):
		self.draw_map_cross()
		if self.move:	print("Move !")
		self.talker(2*(1-self.move))
	def callback_lidar(self,data):
		global time_fps
		fps = int(1/(time.time()-time_fps))
		time_fps = time.time() 
		#print("FPS", fps)
		#self.allow_cross = True
		#self.allow_over = False
		if self.allow_over or self.allow_cross:
			for i in range(360):
				d = data.ranges[i]
				if d == float("inf"): d = 100
				self.data_lidar[0][i] = d
				if i < 180:	self.data_lidar[1][i] = i
				elif i > 180:	self.data_lidar[1][i] = i - 360
				else:	self.data_lidar[1][i] = 0
			if self.allow_over:		self.over_pro()
			elif self.allow_cross:	self.cross_pro()
		else:
			self.talker(0)
		#cv2.imshow('lidar1', self.image_draw)
		#self.img_rec = self.image_draw
		#cf.out.write(self.img_rec)
		#k = cv2.waitKey(5)
	
	def callback_error_center(self, data):
		if data.data == 400.0:
			self.allow_over = False
			self.allow_cross = False
		elif data.data == 450.0:
			self.allow_cross = True
			self.allow_over = False
		else:
			self.allow_over = True
			self.allow_cross = False
			self.error_center = data.data
		
		
if __name__ == '__main__':
	try:
		rospy.init_node('lidar_stream')
		rospy.loginfo("start")
		lidar_pro()
		rospy.spin()
	except KeyboardInterrupt:
		print("Shutting down")
	cv2.destroyAllWindows()
	cf.out.release()
