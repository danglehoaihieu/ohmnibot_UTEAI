#!/usr/bin/env python3
# license removed for brevity
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

import imutils
import math

rospy.init_node('obs', anonymous=True, disable_signals=True)

fps = 0
time_fps = time.time()

data_lidar = np.zeros(shape=[2, 360], dtype = np.float)
image_draw = np.zeros((140, 120, 3), np.uint8)
field_g = np.zeros((700, 600, 3), np.uint8)
dt_imu = time.time()
gyro_z = 0
wz = 0.0
last_gyro_z = 0.0
one = True
offset_ve = 0
dem = 0
yawOld = 0
yawAngle = 0

scale = 50
THRESHOLD_1 = 1
w = 0.2*scale
d_max = 2*scale
safe_dis1 = 0.5*scale # khoang cach bam duoi (Y)
safe_dis2 = 1.5*scale # Khoang cach phia truoc (Y)
safe_dis3 = 0.2*scale # khoang cach so voi vat can theo truc X
yawOld = 0
carX = 60
carY = 100
obs = []

#########
angle_min = 150 # >0
angle_max = -150 # <0
de2ra = 0.0174533
scale = 50
THRESHOLD_1 = 1

bphai = 0.3
btrai = 0.3
bxa = 1
bsau = 0.5

yes_obstacle = 0
steer_lidar = 0.0
speed_lidar = 0.0
speed_max = 15

allow_change_lane = True
allow_overtake = True
waiting = False

counter_signs = 0

running = True 

def cal_angle(point1, point2): # tinh he so goc, suy ra goc cua duong thang voi truc X
	theta = 0.0
	if abs(point1[0]-point2[0]) == 0: # neu x1 = x2 thi goc la 90 do
		return 90
	else:
		#print("point1, point2", point1[0], point1[1], point2[0], point2[1])
		theta = math.atan(float(float(point1[1]-point2[1])/float(point1[0]-point2[0])))*57.2957
		if theta < 0: # neu theta < 0 thi quy doi ve goc tu (>90)
			return 180+theta
	return theta

def calculate_dis(point1, point2): # tinh do dai cua cac canh
	dis = 0.0
	dis = math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)
	#print("dis", dis)
	if dis >= 15 and dis <= 35: # chi lay nhung canh co do dai > 15
		return True
	else:
		return False
def calculate_d_k(ob):
	global carX, carY
	if ob[0] == 0 or ob[0] == 1:
		med_x = (ob[1][0]+ob[2][0]+ob[3][0])//3
		med_y = (ob[1][1]+ob[2][1]+ob[3][1])//3
		d = math.sqrt((med_x-carX)**2 + (med_y-carY)**2)
		
		if med_y != carY:
			theta = math.atan(float(carX-med_x)/float(carY- med_y))
		else:
			if med_x <= carX:
				theta = 1.57
			else:
				theta = -1.57
		return d, theta*57.2957795131
	else:
		med_x = (ob[1][0]+ob[2][0])//2
		med_y = (ob[1][1]+ob[2][1])//2
		d = math.sqrt((med_x-carX)**2 + (med_y-carY)**2)
		
		if med_y != carY:
			theta = math.atan(float(carX-med_x)/float(carY-med_y))
		else:
			if med_x <= carX:
				theta = 1.57079632679
			else:
				theta = -1.57079632679
		return d, theta*57.2957795131

def polyfit_line(points): # polyfit tim duong thang di qua tap diem da duoc loc
	x = []
	y = []
	m, b = 0.0, 0.0
	for i in range(len(points)):
		x.append(points[i][0])
		y.append(points[i][1])
	m, b = np.polyfit(x, y, 1)
	y1 = max(y)
	y2 = min(y) # gan
	temp = 0
	if abs(y1-100) > abs(y2-100): # tim diem gan xe hon, 100 la yCar
		temp = y2
		y2 = y1
		y1 = temp
	x1 = x[y.index(y1)]
	x2 = x[y.index(y2)]
	return (x1, y1), (x2, y2) # (x1, y1) la diem gan xe hon (x2, y2)

def draw_map():
	global data_lidar, angle_min, angle_max, bphai, btrai, bxa, bsau, obs, image_draw
	
	image = np.zeros((140, 120, 3), np.uint8)
	x0 = 60
	y0 = 100
	dist = data_lidar
	for i in range(angle_min, angle_max, -1):
		x = 0
		y = 0
						
		if dist[0][i] < 100: 
			x = int(x0 - scale*dist[0][i]*math.sin(dist[1][i]*de2ra))
			y = int(y0 - scale*dist[0][i]*math.cos(dist[1][i]*de2ra))
			cv2.circle(image, (x, y), 5, (255, 255, 255), -1)
	# cat vung roi
	# khoang cach duoc scale 50:1
	# vd: 50 la 1 met ngoai thuc te
	
	
	#phai = 0.8 #met
	#trai = 1
	#xa = 2
	#sau = 1
	
	phai = int(bphai*50)
	trai = int(btrai*50)
	xa = int(bxa*50) 
	sau = int(bsau*50)
	
	mask_roi = np.zeros((140, 120, 3), np.uint8)
	mask_roi2 = np.ones((140, 120, 3), np.uint8)*255 
	roi = np.array([[(x0-trai, y0+sau), (x0-trai, y0-xa), (x0+phai, y0-xa), (x0+phai, y0+sau)]], dtype=np.int32)
	roi2 = np.array([[(x0-10, y0+10), (x0-10, y0), (x0+10, y0), (x0+10, y0+10)]], dtype=np.int32)
	mask_roi = cv2.fillPoly(mask_roi, roi, (255, 255, 255))
	mask_roi2 = cv2.fillPoly(mask_roi2, roi2, (0, 0, 0))
	image = cv2.bitwise_and(image, mask_roi) 
	image = cv2.bitwise_and(image, mask_roi2)		
	# tien xu ly
	gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray_image = cv2.GaussianBlur(gray_image, (3, 3), 0)
	# loc ra mau trang (220, 255)
	mask_white = cv2.inRange(gray_image, 210, 255)
	
	# findcontours de phan vung cac vat can
	cnts = cv2.findContours(mask_white, cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
		
	# chuyen doi sang maxtri diem bao quanh vat can
	cnts = imutils.grab_contours(cnts)

	cv2.line(image, (x0-trai, y0+sau), (x0-trai, y0-xa), (0,255,255),2 )
	cv2.line(image, (x0+phai, y0-xa), (x0+phai, y0+sau), (0,255,255),2 )
	cv2.circle(image, (x0, y0), 3, (0, 0, 255), -1)
	obs = []
	if cnts is not None:
		for cnt in cnts:
			if len(cnt) > 15 and len(cnt) < 100: # bo di nhung contours co it hon 13 diem --> bo nhung vat nho
			 
				# determine the most extreme points along the contour
				extLeft = tuple(cnt[cnt[:, :, 0].argmin()][0])	# diem ngoai cung ben trai
				extRight = tuple(cnt[cnt[:, :, 0].argmax()][0])	# diem ngoai cung ben phai
				extTop = tuple(cnt[cnt[:, :, 1].argmin()][0]) 	# diem tren cung
				extBot = tuple(cnt[cnt[:, :, 1].argmax()][0])  	# diem duoi cung
				cv2.drawContours(image, [cnt], -1, (0, 255, 255), 2) # ve duong bao (mau vang)
				
				cv2.circle(image, extLeft, 3, (0, 0, 255), -1) 
				cv2.circle(image, extRight, 3, (0, 255, 0), -1)
				cv2.circle(image, extTop, 3, (255, 0, 0), -1)
				cv2.circle(image, extBot, 3, (255, 255, 0), -1)
				theta = [] # khai bao list theta: goc cua cac canh voi truc X
				max_a=0 
				points = [extLeft, extRight, extTop, extBot] # list cac dau mut cua vat
				index = [] # 	list chi so tuong ung cua cac duong
					   #	quy uoc: 0:extLeft, 1:extRight, 2:extTop, 3:extBot
				points_n = [] # list cac diem cua vat can co 2 canh
				detas = [] #
				for i in range(4): # 4 diem -> 6 doan thang
					for ii in range(i+1,4):
						# kiem tra do dai 6 doan thang
						# chi lay doan thang co do dai > 25
						a = calculate_dis(points[i], points[ii])
						if a:
							# tinh va them goc vao list theta
							theta.append(cal_angle(points[i],points[ii]))
							# them chi so tuong cung voi cac diem vao list index
							# index dung de truy xuat nguoc lai: tu goc -> 2 diem
							index.append((i,ii))
				#print("index", index)
				l = len(theta)
				count0 = 0
				count1 = 0
				yes_square = False 	# flag co goc (co 2 canh)
				only_horizontal = False # flag chi co canh ngang : abs(theta) <= 25 or abs(theta-180) <= 25
				only_vertical = False 	# flag chi co canh thang duong abs(theta-90) <= 25
				# phan loai cac cac vat can:
				# 0. yes_square
				# 1. only_horizontal
				# 2. only_vertical
				# 3. canh xien (truong hop con lai)
				for y in range(l): 
					check_hor = False
					if (abs(theta[y]) <= 15) or (abs(theta[y]-180) <= 15): #duong nam ngang
						count0 += 1 # dem so cac duong nam ngang
						check_hor = True # kiem tra la duong nam ngang
								 # de sap xep
					elif abs(theta[y]-90) <= 15: #duong thang dung
						count1 += 1 # dem so cac duong thang dung
					# xet goc tuong doi giua 2 duong thang:
					# deta = abs(deta1 - deta2)
					# neu 2 duong thang gan nhu vuong goc thi abs(deta-90) <= 10
					# neu co 2 duong vuong goc thi break luon!
					for yy in range(y+1, l):
						deta = abs(theta[y] - theta[yy])
						
						if abs(deta-90) <= 10:
							yes_square = True
							# them duong nam ngang truoc tien
							if check_hor:
								# index[y] la goc cua duong nam ngang
								# index[yy] la goc cua duong thang dung
								points_n.append(points[index[y][1]])
								points_n.append(points[index[y][0]])
								points_n.append(points[index[yy][0]])
								points_n.append(points[index[yy][1]])
							else:
								points_n.append(points[index[yy][0]])
								points_n.append(points[index[yy][1]])
								points_n.append(points[index[y][1]])
								points_n.append(points[index[y][0]])
							break # stop vong lap for yy
					if yes_square:
						break # stop vong lap for y
						
					elif count0 >= l-1: # vat gan nhu chi toan duong nam ngang 
						only_horizontal = True
						
					elif count1 >= l-1: # vat gan nhu chi toan duong thang dung
						only_vertical = True	
						
				if yes_square: # 0, 1
					#print("co 2 canh...")
					# ve 2 canh cua vat can
					cv2.line(image, (points_n[0]), (points_n[1]), (0,255,0),2 ) # canh mau xanh la cay
					cv2.line(image, (points_n[2]), (points_n[3]), (0,255,0),2 )
					# append data cua vat can 
					# obs: obs[i][0]-> chi so, obs[i][2] duong ngang, obs[i][1] duong dung
					index = 0
					for i in range(4):
						if points_n.count(points_n[i]) > 1:
							index = i
							break	
					corner = points_n[index]
					while points_n.count(corner) > 0:
						points_n.remove(corner)
					if corner[1] > points_n[1][1]:
						obs.append((1, points_n[0], points_n[1], corner)) # gap duoi xe (vat can)
					else:
						obs.append((0, points_n[1], points_n[0], corner)) #gap dau xe
				elif only_horizontal: # 2
					#print("chi co canh nam ngang....")
					# tim polyfit canh di qua cac diem
					(x1, y1), (x2, y2) = polyfit_line(points)
					cv2.line(image, (x1, y1), (x2, y2), (0,255,0),2 ) # canh mau xanh la cay
					# obs: obs[i][0]->chi so, obs[i][1]->diem gan, obs[i][2]->diem xa			
					obs.append((2, (x1, y1), (x2, y2)))
				elif only_vertical: # 3
					#print("chi co canh thang dung....")
					# C1: co the tim canh bang poly fit
					# C2: lay 2 diem Top va Bot
					(x1, y1) = points[2] # point Bot -> diem gan xe hon
					(x2, y2) = points[3] # point Top -> diem o xa xe
					
					cv2.line(image, (x1, y1), (x2, y2), (0,255,0),2 ) # canh mau xanh la cay
					
					# obs: obs[i][0]->chi so, obs[i][1]->diem gan, obs[i][2]->diem xa				
					obs.append((3, (x2, y2), (x1, y1)))
				elif len(index) > 0: # 4
					#print("canh xien")
					# dung polyfit tim canh di qua cac diem
					(x1, y1), (x2, y2) = polyfit_line(points)
					cv2.line(image, (x1, y1), (x2, y2), (0,255,0),2 ) # canh mau xanh la cay
					# obs: obs[i][0]->chi so, obs[i][1]->diem gan, obs[i][2]->diem xa
					obs.append((4, (x1, y1), (x2, y2)))
	'''	
	d_k = []
	for i in range(len(obs)):
		d, theta = calculate_d_k(obs[i])
		d_k.append(d)
	a = min(d_k)
	i = 
	'''
	image_draw = image
	#cf.draw = False
	#cf.analysis = True

#########


def calculate_phi_k(ob):
	global carX, carY
	x1 = ob[1][0]
	y1 = ob[1][1]
	x2 = ob[2][0]
	y2 = ob[2][1]
	
	d1 = math.sqrt((x1-carX)**2 + (y1-carY)**2)
	d2 = math.sqrt((x2-carX)**2 + (y2-carY)**2)
	d3 = math.sqrt((x1-x2)**2 + (y1-y2)**2) + w # w la chieu rong cua xe
	try:
		phi = math.acos((d1**2 + d2**2 - d3**2)/(2*d1*d2))
	except ValueError:
		phi = 1.57079632679
		pass
	
	return phi*57.2957795131

def cal_f_total():
	global obs, yawOld, yawAngle, field_g
	angle = 0.0
	d_k = []
	phi_k = []
	theta_k = []
	alpha_k = []
	angle_add = 0.0
	l = len(obs)
	for i in range(l):
		d, theta = 0.0, 0.0
		d, theta = calculate_d_k(obs[i])
		d_k.append(d)
		theta_k.append(theta)
		phi_k.append(calculate_phi_k(obs[i]))
		range_k = d_max - d
		alpha_k.append(1.6487212707*range_k) 
	if l > 0:	
		min_theta = min(theta_k)
		if min_theta < 8:
			angle_add = 5.0
	f_rep = []
	f_att = []
	f_total = []
	angle_k = []
	gama = 1.5
	goal = yawOld - yawAngle + angle_add
	#goal = 0
	for i in range(90, -91, -1):
		angle_k.append(i)
		att = gama*abs(goal-i)
		f_att.append(att)
		sum_f_rep = 0.0
		if len(phi_k) > 0:
			for k in range(l):
				try:
					sum_f_rep = sum_f_rep +  alpha_k[k]*math.exp(-(float(theta_k[k]-i)**2)/float(0.5*phi_k[k]**2))
				except ZeroDivisionError:
					pass	
				
		f_rep.append(sum_f_rep)
		f_total.append((att+sum_f_rep))
		
	min_f_total = min(f_total)
	index_angle_min = f_total.index(min_f_total)
	angle_f = angle_k[index_angle_min]
	# ve ra de de quan sat
	
	map_f = np.zeros((700, 600, 3), np.uint8)
	for i in range(len(f_total)-1):
		cv2.line(map_f, (i*3, 600-2*int(f_total[i])), ((i+1)*3, 600-2*int(f_total[i+1])), (0,255,0),2)
		cv2.line(map_f, (i*3, 600-2*int(f_rep[i])), ((i+1)*3, 600-2*int(f_rep[i+1])), (255,255,255),1)
		cv2.line(map_f, (i*3, 600-2*int(f_att[i])), ((i+1)*3, 600-2*int(f_att[i+1])), (0,0,255),1)
		if i == index_angle_min:
			cv2.circle(map_f, (i*3, 600-2*int(f_total[i])), 5, (0, 0, 255), -1)
	for i in range(19):
		cv2.line(map_f, (i*30, 600), (i*30, 0), (255,255*(i%2),0), 1)
		cv2.putText(map_f, str(angle_k[i*10]), (i*30-5, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255*(i%2),0), 1, cv2.LINE_AA) 
	cv2.putText(map_f, "steering angle: "+str(angle_f), (145, 650), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2, cv2.LINE_AA) 
	field_g = map_f 
	
	return angle_f
angle = 0.0 # do (-60; 60)
speed = 0.0 # (0; cf.speed_max)	
step_1 = True
step_2 = False
step_3 = False
ck = True
comeback = False

allow_change_lane = True
allow_overtake = True
over_cross = False
count_appe_ob = 0
'''
def plan(x):
	global waiting, over_cross, count_appe_ob, counter_signs
	global steer_lidar, speed_lidar, speed_max
	# phuong an 1: bam duoi
	if x == 1: 
		if counter_signs == "?":
			bphai = 1
			draw_map()
			if len(obs) > 0:
				yes_obstacle = 1
				
		elif counter_signs == "??":
			
	# phuong an 2: khi co xe thi stop, doi cho xe di qua roi di tiep
	if x == 2:
		if counter_signs == "?": # bat dau vao vung co xe
			draw_map()
			l = len(obs)
			if  l > 0:
				yes_obstacle = 1
				speed_lidar = 0
			else:
				yes_obstacle = 0
				speed_lidar = speed_max
		if counter_signs == "?": # da di qua vung co xe
			yes_obstacle = 0
				
'''	
counter = 0
allow_change_lane = False
def obstacle():
	global step_1, step_2, step_3, ck, angle, speed, yes_obstacle, bphai, obs, yawOld, yawAngle, image_draw
	global steer_lidar, speed_lidar, speed_max, comeback, allow_change_lane, allow_overtake, bxa
	global waiting, counter, carX, carY
	#plan(1)
	draw_map()
	l = len(obs)
	if l > 0:
		yes_obstacle = 1
		bphai = 1
		for i in range(1):
			x = obs[i][0]
			print("x= ", x)
			if step_1: # o dang sau xe
				if not allow_change_lane: # bam theo duoi 
					bphai = 0.8
					bxa = 1.2
					print("bam duoi")
					if x == 0:
						(x1, y1) = obs[i][1]
						(x2, y2) = obs[i][3]
					elif x == 2:
						(x1, y1) = obs[i][1]
						(x2, y2) = obs[i][2]
					elif x == 3 or x == 4 or x == 1:
						(x1, y1) = obs[i][1]
						(x2, y2) = obs[i][1]
					(x0, y0) = (float((x1+x2)/2), float((y1+y2)/2))
					angle = 57.2957795131 * math.atan(float((x0-carX)/(carY-y0)))
					print("speed", speed)
					speed = (carY - y0) - safe_dis1
				else:# chuyen sang lan trai
					bphai = 1
					bxa = 1.2
					angle_max = -160
					print("chuyen lan", yawOld, yawAngle)
					
					if ck:
						yawOld = yawAngle
						ck = False
					angle = -2*cal_f_total()
					speed = 0.8*speed_max
					
					if x == 3 or x == 4:# thay dau xe/suong xe
						
						print("obs[i][2]", obs[i][2][1])
						if obs[i][2][1] >= carY-5:
							counter += 1
							if counter > 5:
								step_1 = False
								step_3 = True
								ck = True
								counter = 0
					
			elif step_2: # song song
				#print("chay song song")
				bphai = 0.8
				bxa = 1
				if x == 1 or x == 0: 
					(x2, y2) = obs[i][2]
					corner = obs[i][3]
				elif x == 3 or x == 4:
					corner = obs[i][1]
					(x2, y2) = obs[i][2]
				if x != 2:
					cv2.line(image_draw, (x2, y2), corner, (255,255,255),4 ) # canh mau xanh la cay
					y0 = corner[1] - 60
					x0 = int(-50*(corner[0] - x2)/(corner[1] - y2-0.5) + corner[0]) 
					center = x0 - safe_dis3
					cv2.circle(image_draw, (int(center), y0), 5, (0, 0, 255), 2)
					angle = 57.2957795131 * math.atan(float(float(center-carX)/50))
					speed = (carY-y0) - (safe_dis2)
				if allow_overtake: 
					if x == 1 or x == 2: # thay dau xe
						step_2 = False
						step_3 = True
	
	else:
		bphai = 0.3
		yes_obstacle = 0
		steer_lidar = 0.0
		speed_lidar = 0.0
		step_1 = True
		step_2 = False
		step_3 = False	
		angle_max = -150

	if step_3: # vuot xe, tro ve lane cu
		bxa = 1
		yes_obstacle = 1
		print("dang vuot len")
		print("obs[i][2]", obs[i][2][1])
		angle = 120
		speed = speed_max
		angle_max = -150
		#step_3 = False
		#step_1 = True
					
	steer_lidar = angle
	speed_lidar = speed				

def get_yaw(data):
	global yawAngle
	yawAngle = data.data

def callback_lidar(data):
	range_angels = np.arange(len(data.ranges))
	global data_lidar
	for i in range(360):
		d = data.ranges[i]
		if d == float("inf"):
			d = 100
		data_lidar[0][i] = d
		if i < 180:
			data_lidar[1][i] = i
		elif i > 180:
			data_lidar[1][i] = i - 360
		else:
			data_lidar[1][i] = 0
def get_signs(data):
	global counter_signs
	counter_signs = data.data	       
def pub(array):
	publisher = rospy.Publisher('/obstacle', Float32MultiArray, queue_size=1)
	d = Float32MultiArray(data=array)
	publisher.publish(d)
def main():
	global running, fps, time_fps, yes_obstacle, steer_lidar, speed_lidar
	print("Main started!")
	while running:
		fps = int(1/(time.time()-time_fps))
		time_fps = time.time()
		#print(fps)
		obstacle()
		pub([yes_obstacle, steer_lidar, speed_lidar])

def show():
	global running, image_draw
	print("Show_thread started !")
	while running:
		cv2.imshow('lidar', image_draw)
		cv2.imshow('field', field_g)
		k = cv2.waitKey(5)
		if k == ord('q'):
			running = False
			rospy.signal_shutdown("shutdown")
def listenner():
	rospy.Subscriber("/yaw", Float32, get_yaw, queue_size=1)
	rospy.Subscriber("/scan", sensor_msgs.msg.LaserScan, callback_lidar, queue_size = 1)
	#rospy.Subscriber("/counting_signs", Int32, get_signs, queus_size=1)


main_thread = threading.Thread(name= "main_thread", target= main)
main_thread.start()
show_thread = threading.Thread(name= "show information", target= show)
show_thread.start()

listenner()

