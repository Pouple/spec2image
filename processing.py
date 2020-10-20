import os 
import math
import scipy
import numpy as np 
import matplotlib.pyplot as plt 

from scipy import signal
from skimage.measure import block_reduce

import settings as sett

paths = sett.paths()
params = sett.parameters()

def fast_fourier(sample, samplerate):
	""" Compute a Fast Fourier Transform for visualization purposes

	Parameters
	----------
	sample : array
		Array containaing the raw signal
	samplerate : int
		Number of sample in the signal per unit of time

	Returns
	-------
	array
		Fast-Fourier Transform of the signal

	"""
	fft = scipy.fft(sample)

	return fft

def implant_projection(tmaps, single_map=False):
	""" Downscale the final cortical stimulation to match capacitty of the implant

	Parameters
	----------
	tmaps : array
		Images to project to the cortex. Shape must be (time_points, maps, width, height) if singlemap=True
	single_map : bool
		Optional argument in case of a single tonotopic map passed as arg

	Returns
	-------
	array
		Images downsclaed to send to implant. Shape is (time_point, width, height)

	"""
	# Average stimulation pattern over frequencies to get weighted map
	if single_map:
		tmaps = np.mean(tmaps, axis=1)
	
	width_cut = tmaps.shape[1] % params.size_implant
	height_cut = tmaps.shape[2] % params.size_implant

	# Cut excess borders
	tmaps = tmaps[:, width_cut:, height_cut:]

	tmap_implant = block_reduce(tmaps, block_size=(1, tmaps.shape[1] // params.size_implant, tmaps.shape[2] // params.size_implant), func=np.mean)

	return tmap_implant

def spectro(sample, samplerate, window_ms=20, overlap=50):
	window_size = int(window_ms * samplerate * 0.001)
	overlap_size = overlap * 0.01* window_size

	spectrum, frequencies, times, im = plt.specgram(sample, Fs=samplerate, 
													NFFT=window_size, noverlap=overlap_size)


	plt.title('Spectrogram of sound sample')
	plt.yscale('log')
	plt.ylim((1, int(samplerate / 2)))
	plt.xlabel('Time (sec)')
	plt.ylabel('Frequency (Hz)')

	plt.savefig(os.path.join(paths.path2Output, 'sample_spectrogram.png'))
	plt.close()

	return spectrum, frequencies, times

def downscale_tmaps(tmaps, block_size=(4, 4)):
	tmaps_reduced = []
	for i, tmap in enumerate(tmaps):
		tmap_reduced = block_reduce(tmap, block_size=block_size, func=np.mean)
		tmaps_reduced.append(tmap_reduced)

	return np.array(tmaps_reduced)

def rectangle_stim(tmap4, tmap32, n_rectangles, width_rect=0.4, squared=False):
	# Get minima
	min_1 = np.unravel_index(tmap4.argmax(), tmap4.shape)
	min_2 = np.unravel_index(tmap32.argmax(), tmap32.shape)

	if squared:
		tmap4, tmap32 = tmap4**2, tmap32**2


	weighted_tmap = tmap32 - tmap4

	distance_min = math.sqrt((min_1[0] - min_2[0])**2 + (min_1[1] - min_2[1])**2)
	
	vector = np.array([min_2[0] - min_1[0], min_2[1] - min_1[1]])
	v_alpha = vector * 1 / n_rectangles
	v_theta = np.array([vector[1], - vector[0]]) * width_rect

	rect_stim = []
	for i in range(n_rectangles):
		origin = np.array([min_1[0], min_1[1]]) + i * v_alpha

		rect = np.array([[origin[0] - v_theta[0], origin[1] - v_theta[1]],
						 [origin[0] - v_theta[0] + v_alpha[0], origin[1] - v_theta[1] + v_alpha[1]],
						 [origin[0] + v_theta[0] + v_alpha[0], origin[1] + v_theta[1] + v_alpha[1]],
						 [origin[0] + v_theta[0], origin[1] + v_theta[1]]])

		
		idx_x = np.arange(int(np.min(rect[:, 0])), int(np.max(rect[:, 0])))
		idx_y = np.arange(int(np.min(rect[:, 1])), int(np.max(rect[:, 1])))


		edges = np.array([[rect[j-1], rect[j]] for j in range(4)])

		inside = []
		for idx in idx_x:
			for idy in idx_y:
				score = 0
				for edge in edges:
					D = (edge[1, 0] - edge[0, 0]) * (idy - edge[0, 1]) - (idx - edge[0, 0]) * (edge[1, 1] - edge[0, 1])
					if D < 0:
						score += 1
				if score == 4:
					inside.append([int(idx), int(idy)])
		rect_stim.append(np.array(inside))
	
	return rect_stim, weighted_tmap, min_1, min_2

def gaussian_windowing(specgram, frequencies):
	freq_series = [specgram[:, i] for i in range(specgram.shape[1])]

	# Define windows for gaussian windowing
	gaussian_windows = [signal.gaussian(math.log(f/1000, 2)*1000, math.log(f/1000, 2)*150) for f in params.freqs]

	# Get indices of frequencies of interest
	freq_idxs = [np.where(np.logical_and(frequencies >= params.freqs[i]-len(win)/2, frequencies < params.freqs[i]+len(win)/2)) 
						for i, win in enumerate(gaussian_windows)]
	win_idxs = [np.array(frequencies[idx] - np.min(frequencies[idx])).astype(int) for idx in freq_idxs]

	magnitudes = []
	for i, freq in enumerate(freq_series):
		magnitudes.append([np.sum(freq[freq_idxs[i]] * win[win_idxs[i]]) for i, win in enumerate(gaussian_windows)])

	magnitudes = np.array(magnitudes)
	magnitudes = magnitudes/np.max(magnitudes)

	return magnitudes

