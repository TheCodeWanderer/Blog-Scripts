""" Loads a SOFA file and visualizes the HRTF amplitude and phase """
#%% Load SOFA file

from SOFASonix import SOFAFile
import numpy as np
import matplotlib.pyplot as plt
import scipy.fft

filename='hrtf_M_hrtf B.sofa'
sofa = SOFAFile.load(filename)

#Get params/data
SR = sofa.Data_SamplingRate
delay = sofa.Data_Delay
pos = sofa.SourcePosition
IR = sofa.Data_IR
N = sofa._N

#%% FFT along equator
ind = pos[:,1]==0 #select where the elevation is zero
pos_pol = pos[ind,0] #only the polar plane (at constant radius and elevation)
IR_pl = IR[ind,:,:] #Filter IR based on the above criteria
ind2 = np.argsort(pos_pol) #sort values to prevent artifcats during plotting
pos_pol = pos_pol[ind2]
IR_pl = IR_pl[ind2,:,:]
xf = scipy.fft.rfftfreq(N,1/SR)
yf = scipy.fft.rfft(IR_pl)

#%% amplitude
plt.pcolormesh(xf,pos_pol,np.abs(yf[:,0,:]),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Left Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Azimuthal angle (deg.)')
plt.xlim([0, 18000])

plt.figure()
plt.pcolormesh(xf,pos_pol,np.abs(yf[:,1,:]),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Right Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Azimuthal angle (deg.)')
plt.xlim([0, 18000])

#%% phase
plt.figure()
plt.pcolormesh(xf,pos_pol,np.arctan2(np.imag(yf[:,0,:]),np.real(yf[:,0,:])),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Left Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Azimuthal angle (deg.)')
plt.xlim([0, 18000])

plt.figure()
plt.pcolormesh(xf,pos_pol,np.arctan2(np.imag(yf[:,1,:]),np.real(yf[:,1,:])),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Right Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Azimuthal angle (deg.)')
plt.xlim([0, 18000])

#%% FFT along polar (xz-plane)
ind = pos[:,0]==0 #select where the azimuth is zero
pos_pol = pos[ind,1] #only the polar plane (at constant radius and elevation)
#IR_pl = IR[ind,:,:] #Filter IR based on the above criteria
IR_pl = IR[ind,:,:] #Filter IR based on the above criteria
ind2 = np.argsort(pos_pol) #sort values to prevent artifcats during plotting
pos_pol = pos_pol[ind2]
IR_pl = IR_pl[ind2,:,:]
xf = scipy.fft.rfftfreq(N,1/SR)
yf = scipy.fft.rfft(IR_pl)

#%% amplitude
plt.figure()
plt.pcolormesh(xf,pos_pol,np.abs(yf[:,0,:]),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Left Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Polar angle (deg.)')
plt.xlim([0, 18000])

plt.figure()
plt.pcolormesh(xf,pos_pol,np.abs(yf[:,1,:]),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Right Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Polar angle (deg.)')
plt.xlim([0, 18000])

#%% phase
plt.figure()
plt.pcolormesh(xf,pos_pol,np.arctan2(np.imag(yf[:,0,:]),np.real(yf[:,0,:])),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Left Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Polar angle (deg.)')
plt.xlim([0, 18000])

plt.figure()
plt.pcolormesh(xf,pos_pol,np.arctan2(np.imag(yf[:,1,:]),np.real(yf[:,1,:])),shading='gouraud',antialiased=True)
plt.colorbar()
plt.title('Right Ear')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Polar angle (deg.)')
plt.xlim([0, 18000])
