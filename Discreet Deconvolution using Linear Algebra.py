# -*- coding: utf-8 -*-
"""
Deconvolute a discreet signal by using linear algebra.

Created on Mon May  9 12:55:17 2022

@author: CodeWanderer
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import linalg
from numpy.linalg import solve, lstsq

#%% PARAMS
L=41 #length of array; seems that the matrix inversion of K is singular (det=0) if both L and ir are odd or even
ir=4 #boxcar radius, should be smaller than L/2
sig = 1e-1 #noise amplitude; at 1e-14 all methods give almost exactly the same residual for some reason.... note that double machine precision is approximately 10^-16 so lower than this is effectively zero

#%% FUNCS
def boxcar(ir,L):
    """ boxcar function evaluated at 1 up to a radius of ir about 0th index; 0 elsewhere """
    y = np.zeros(L)
    y[:ir]=1
    y[-ir+1:]= 0 if ir==1 else 1
    return y

#%% MAIN
#generate convolution kernel
K = np.asarray([np.roll(boxcar(ir,L),i) for i in range (L)])
print(K)

K_inv = linalg.inv(K) #invert the kernel (breaks down for large arrays)
K_inv = linalg.pinv(K) #invert the kernel (breaks down for large arrays)
print(K_inv)

y_true = np.zeros(L) #true function
y_true[L//4] = 3
y_true[L//4+3] = -2
y_true[L//2] = 1
y_true[L//2+4] = 1
y_true[L//2+8] = -1
y_true[L//2-2] = 1
print(y_true)

y_conv = K @ y_true #convoluted function
noise = np.random.normal(0,sig,L) #noise distribution of standard deviation, sig, and mean 0
y_conv = y_conv + noise #Adds noise to convoluted signal (not to pre-convoluted!)

#compare deconvolution techniques
y_inv = K_inv @ y_conv #Multiply by the inverse matrix

y_solve = solve(K, y_conv) #Using numpy solve method

y_lstsq = lstsq(K, y_conv, rcond=None) #solve using least-squares solver

y_box = K[0,:]
y_fft = np.real(np.fft.ifft(np.fft.fft(y_conv)/np.fft.fft(y_box)))

#%% PLOT
plt.figure()
plt.plot(y_true,'.-k',label="true")
plt.plot(y_conv,'.-r',label="conv.")
plt.plot(y_inv,'.--g',label="inv")
plt.legend()
plt.xticks([])
plt.grid(ls='--')
plt.ylabel("value")
#plt.axis("off")

#compare values
plt.figure()
plt.plot(y_true,'.-k',label="true")
plt.plot(y_conv,'.--k',label="conv.")
plt.plot(y_inv,'.-g',label="inv")
plt.plot(y_solve,'.-b',label="solve")
plt.plot(y_lstsq[0],'.-r',label="lstsq")
plt.plot(y_fft,'.-y',label="fft")
plt.legend()
plt.grid(ls='--')
plt.ylabel("value")

#residual plot
plt.figure()
plt.plot(y_inv-y_true,'.-g',label="inv")
plt.plot(y_solve-y_true,'.-b',label="solve")
plt.plot(y_lstsq[0]-y_true,'.-r',label="lstsq")
plt.plot(y_fft-y_true,'.-y',label="fft")
plt.legend()
plt.grid(ls='--')
plt.ylabel("residual")

plt.figure()
plt.plot(K[L//2,:])
plt.plot(K_inv[L//2,:])
