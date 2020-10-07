#!/usr/bin/env python
# coding: utf-8

import os 
import math
import scipy
import numpy as np 
import matplotlib.pyplot as plt 

import plot as pl 
import settings as sett
from functions.Sample import Sound

plt.rcParams['figure.figsize'] = [20, 12]
plt.rcParams['figure.dpi'] 


tonotopic_maps = np.load(os.path.join('../Data/INT_Sebmice_alignedtohorizon.npy'))

tmap4, tmap32 = tonotopic_maps[1], tonotopic_maps[3]

# Normalize tmaps and inverse them
tmap4 = 1 - (tmap4 - np.min(tmap4)) / (np.max(tmap4) - np.min(tmap4))
tmap32 = 1 - (tmap32 - np.min(tmap32)) / (np.max(tmap32) - np.min(tmap32))

# Get minima
min_4 = np.unravel_index(tmap4.argmax(), tmap4.shape)
min_32 = np.unravel_index(tmap32.argmax(), tmap32.shape)

tmap4, tmap32 = tmap4**2, tmap32**2

weighted_tmap = tmap32 - tmap4


def rectangle_stim(tmap, min_1, min_2, n_rectangles, width_rect=0.4):
	distance_min = math.sqrt((min_1[0] - min_2[0])**2 + (min_1[1] - min_2[1])**2)
	
	vector = np.array([min_2[0] - min_1[0], min_2[1] - min_1[1]])
	vector_bin = [vector * 1 / n_rectangles * i for i in range(n_rectangles+1)]
	width_rect = width_rect * distance_min

	rect_stim = []
	for i in range(1, n_rectangles+1):
		rect = np.array([[min_1[0] - width_rect + vector_bin[i-1][0], min_1[1] + vector_bin[i-1][0] + width_rect * vector[0] / vector[1]],
					     [min_1[0] + width_rect + vector_bin[i-1][0], min_1[1] + vector_bin[i-1][0] - width_rect * vector[0] / vector[1]],
					     [min_1[0] + width_rect + vector_bin[i][1], min_1[1] + vector_bin[i][1] - width_rect * vector[0] / vector[1]],
					     [min_1[0] - width_rect + vector_bin[i][1], min_1[1] + vector_bin[i][1] + width_rect * vector[0] / vector[1]]])

		idx_x = np.arange(int(np.min(rect[:, 0])), int(np.max(rect[:, 0])))
		idx_y = np.arange(int(np.min(rect[:, 1])), int(np.max(rect[:, 1])))

		edges = np.array([[rect[j-1], rect[j]] for j in range(4)])

		inside = []
		for idx in idx_x:
			for idy in idx_y:
				score = 0
				for edge in edges:
					D = (edge[1, 0] - edge[0, 0]) * (idy - edge[0, 1]) - (idx - edge[0, 0]) * (edge[1, 1] - edge[0, 1])
					if D > 0:
						score += 1
				if score == 4:
					inside.append([int(idx), int(idy)])
		print(len(inside))

		rect_stim.append(np.array(inside))

	return np.array(rect_stim)



# # Get distance between two minimum
# distance_min = math.sqrt((min_4[0] - min_32[0])**2 + (min_4[1] - min_32[1])**2)

# # Define number of rectangles in stimulation
# n_rectangles = 5

# vector = np.array([min_32[0] - min_4[0], min_32[1] - min_4[1]])
# vector_bin = vector * 1/n_rectangles
# width_rect = 0.4*distance_min

# # Draw rectangle with vertices in order 
# rect = np.array([[min_4[0] - width_rect, min_4[1] + width_rect * vector[0] / vector[1]],
# 				 [min_4[0] + width_rect, min_4[1] - width_rect * vector[0] / vector[1]],
# 				 [min_4[0] + width_rect + vector_bin[0], min_4[1] + vector_bin[1] - width_rect * vector[0] / vector[1]],
# 				 [min_4[0] - width_rect + vector_bin[0], min_4[1] + vector_bin[1] + width_rect * vector[0] / vector[1]]])

# idx_x = np.arange(int(np.min(rect[:, 0])), int(np.max(rect[:, 0])))
# idx_y = np.arange(int(np.min(rect[:, 1])), int(np.max(rect[:, 1])))

# edges = np.array([[rect[i-1], rect[i]] for i in range(4)])

# inside = []
# for idx in idx_x:
# 	for idy in idx_y:
# 		score = 0
# 		for e, edge in enumerate(edges):
# 			D = (edge[1, 0] - edge[0, 0]) * (idy - edge[0, 1]) - (idx - edge[0, 0]) * (edge[1, 1] - edge[0, 1])
# 			if D > 0:
# 				score += 1
# 		if score == 4:
# 			inside.append([int(idx), int(idy)])

# inside = np.array(inside)
rect_stim = rectangle_stim(weighted_tmap, min_4, min_32, 5)
print(rect_stim[0].shape)

weighted_tmap[rect_stim[2, :, 1], rect_stim[2, :, 0]] = 1


# Script for checking
for edge in edges:
 	plt.plot(edge[:, 0], edge[:, 1])
plt.scatter(rect[:, 0], rect[:, 1])
plt.scatter(min_4[0], min_4[1], marker='o', c='red')
plt.scatter(min_32[0], min_32[1], marker='o', c='red')
plt.plot([min_4[0], min_32[0]], [min_4[1], min_32[1]])
plt.imshow(weighted_tmap, cmap='coolwarm')

plt.show()


# In[ ]:




