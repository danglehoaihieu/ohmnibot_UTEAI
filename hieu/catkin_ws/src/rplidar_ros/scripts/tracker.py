#!/usr/bin/env python3
from filterpy.common import Q_discrete_white_noise
from filterpy.kalman import KalmanFilter
from scipy.linalg import block_diag
import numpy as np
import cv2

class Tracker():

    def __init__(self, dt=1.0/20.0):
        self.dt = dt

        self.kalman = KalmanFilter(dim_x=4, dim_z=2)
        # self.kalman.x = np.array([
        #     [0],
        #     [0],
        #     [0],
        #     [0]
        # ])

        # uncertaintyInit = 500
        # self.kalman.P = np.array([
        #     [1, 0, 0, 0],
        #     [0, 1, 0, 0],
        #     [0, 0, 1, 0],
        #     [0, 0, 0, 1]
        # ]) * uncertaintyInit

        # processVariance = 30
        # q = Q_discrete_white_noise(dim=2, dt=self.dt, var=processVariance)
        # self.kalman.Q = block_diag(q, q)

        
        # self.kalman.R = np.array([
        #     [50, 0],
        #     [0, 50]
        # ])
        
        # self.kalman.H = np.array([
        #     [1, 0, 0, 0],
        #     [0, 0, 1, 0]
        # ])
        
        # self.kalman.F = np.array([
        #     [1, dt, 0, 0],
        #     [0, 1, 0, 0],
        #     [0, 0, 1, dt],
        #     [0, 0, 0, 1]
        # ])
        self.kalman.F=np.array([ [1 ,0,dt,0] , [0,1,0,dt] , [0,0,1,0] , [0,0,0,1] ])
 
        #Initial State cov
        self.kalman.P= np.identity(4)*400
         
        #Process cov
        self.kalman.Q= np.identity(4)*0.05
         
        # #Control matrix
        self.kalman.B=np.array( [ [0] , [0], [0] , [0] ])
         
        # #Control vector
        self.kalman.U=0
         
        #Measurment Matrix
        self.kalman.H  = np.array([ [1, 0, 0, 0], [ 0, 1, 0, 0]])
         
        #Measurment cov
        self.kalman.R= np.identity(2)*30         
        # Initial State
        self.kalman.x = np.array( [[0],[0],[0],[0]] )
    def add(self, poly):
        
        
        if (poly):
            self.kalman.predict()
            m = poly[0]
            b = poly[1]
            measurement = np.array([
                [m],
                [b]
            ], np.float32)
            self.kalman.update(measurement)
        else:
            self.kalman.x=self.kalman.x_prior
           
        #line = np.poly1d([self.kalman.x[0, 0], self.kalman.x[1, 0]])
        return (int(self.kalman.x[0,0]), int(self.kalman.x[1, 0]))
