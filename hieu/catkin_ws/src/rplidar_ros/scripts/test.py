import cv2
import numpy as np
import time
deg2rad = 0.01745329251
def rotate_point(center, angle, point):
	cx = center[0]
	cy = center[1]
	s = np.sin(angle*deg2rad);
	c = np.cos(angle*deg2rad);
	px = point[0]
	py = point[1]
	# translate point back to origin:
	px -= cx
	py -= cy
	# rotate point
	xnew = px * c - py * s
	ynew = px * s + py * c
	# translate point back:
	px = xnew + cx
	py = ynew + cy
	return (px,py)

image = np.zeros((240,320,3), np.uint8)
img = image.copy()

roi2=np.array([[(50,50),(100,50),(100,120),(50,120)]],dtype=np.int32)
roi = [(50,50),(100,120)]
rec = cv2.rectangle(image, (50,50), (100,120), (255,255,255), 2)
center = (80, 150) 
t = time.time()
for i,p in enumerate(roi2[0]):
	roi2[0][i] = rotate_point(center=center, angle=80, point=p)
print('t', time.time()-t)
#M = cv2.getRotationMatrix2D(center, 45, 1.0)
#roi2 = cv2.warpAffine(roi2, M, (320,240))
cv2.drawContours(img, roi2, -1, (255,255,255), 2)
cv2.imshow("res", image)
#cv2.imshow("rotate rec", rotated)
cv2.imshow("img", img)

k = cv2.waitKey(0)
if k == ord('q'):
	cv2.destroyAllWindows()
