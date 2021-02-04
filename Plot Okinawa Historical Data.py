# -*- coding: utf-8 -*-
"""
Created on Wed Jul  1 21:24:27 2020

@author: Ivan
"""
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from datetime import datetime
#from getdist import plots, MCSamples
#plt.switch_backend("Qt5Agg")

def getsubdata(DATA,month,period):
    """
    month : 1,...,12
    period : 0,1,2,3 (0am,6am,12pm,6pm)
    """
    months = [date.month==month for date in dates] #Bollean array indicating True for the specified month
    DoM = DATA[months][:,period] #Data for each day of the specified month for all years
    dates_month = dates[months] #datetime object for specifed month
    
    #%Calculate statistics by day
    if month==2:
        dm=28
    elif month in [4,6,9,11]:
        dm=30
    else:
        dm=31

    days = np.arange(dm)+1
    # d.day==day for d in dates_month gives True for where the datetime day component is equal to day
#    DoM_avg = [np.mode(DoM[[d.day==day for d in dates_month]]) for day in days] #Median value (since distribution could be uneven)
#    DoM_std = [np.std(DoM[[d.day==day for d in dates_month]]) for day in days] #Standard deviation about the mean (use hist method)
    return [DoM[[d.day==day for d in dates_month]] for day in days] #DATA[month][day]

def supylabel(fig,label):
    fig.text(0.04, 0.5, label, va='center', rotation='vertical', size=20)
    
def supxlabel(fig,label):
    fig.text(0.5, 0.04, label, ha='center', size=20)

def makeplot(STAT,ymax,title,ylabel,xlabel):
    dmean = lambda i : [np.mean(x) for x in STAT[i]] #mean of the data set
    derr = lambda i,v : np.asarray([(m-np.mean(x[x<m]), np.mean(x[x>m])-m) for x,m in zip(STAT[i],v)]).T #calculate the error bounds by taking the mean of the values greater/lower than the mean of the total data set

    fig, axs = plt.subplots(nrows=3, ncols=4, sharex=True, sharey=True,figsize=(12,8))
    fig.suptitle(title, size=26)
    supylabel(fig,ylabel)
    supxlabel(fig,xlabel)
    
    axsf = axs.flatten()
    for i in range(12):
        daily_mean = dmean(i)
        daily_err = derr(i,daily_mean)
        axsf[i].errorbar(days[:len(daily_mean)], daily_mean, yerr=daily_err,lw=1,zorder=1)
        axsf[i].plot(days[:len(daily_mean)], daily_mean,'.-')
        for j,x in enumerate(STAT[i]):
#            V,P = KernelDensity(x,None,None)
#            cLines(axsf[i],(j+1)*np.ones(len(V)),V,P)
            axsf[i].scatter((j+1)*np.ones(len(x)),x,alpha=0.25,s=8,c='k',edgecolors='none')
        axsf[i].axhline(y=np.mean(daily_mean),ls='--',c='k')
        axsf[i].set_ylim(bottom=0, top=ymax)
        axsf[i].set_xlim(left=0, right=32)
        axsf[i].set_xticks(days[::3])
        axsf[i].tick_params(axis="x",direction="in")
        axsf[i].set_title(monthlbl[i], position=(0.5, 0.975),size=16)
    fig.subplots_adjust(top=0.899,
                        bottom=0.131,
                        left=0.116,
                        right=0.932,
                        hspace=0.128,
                        wspace=0.047)
						
def cLines(axs,x,y,c):
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    norm = plt.Normalize(c.min(), c.max())
    lc = LineCollection(segments, cmap='Greys', norm=norm)
    # Set the values used for colormapping
    lc.set_array(c)
#    lc.set_linewidth(2)
    axs.add_collection(lc)

	#def KernelDensity(samps,xl,xu):
#    """ Optimized Kernel Density Estimation - automated optimal bandwidth 
#    choice for 1D and 2D densities (Botev et al. Improved Sheather-Jones 
#    method), with boundary and bias correction.
#    https://getdist.readthedocs.io/en/latest/index.html
#    
#    ***need to preset the bandwidth to solve some issues...
#    """
#    with_range = MCSamples(samples=samps, names=['x'],
#                       settings = {'mult_bias_correction_order':1}, 
#                       ranges={'x':[xl,xu]})
##    try:
#    dens = with_range.get1DDensity('x',kwargs={'smooth_scale_1D':0.9})
##    except:
##        print(samps)
##        return None,None
#    V = dens.x #Values
#    P = dens.Prob(V) #Probabilities
#    return V,P

#%%Load Data
file = "Okinawa_ToriiBeach_GFS13_Wind_Temp_Rain_Cloud.txt"
str2date = lambda x: datetime.strptime(x.decode("utf-8"), '%d.%m.%Y')
load = lambda x: np.genfromtxt(file,usecols=x, delimiter="\t",filling_values=0,comments='#',skip_header=2)

WIND = load((1,2,3,4))
TEMP = load((5,6,7,8))
RAIN = load((9,10,11,12))
CLOU = load((13,14,15,16)) #cloud data
dates = np.genfromtxt(file, usecols=0,converters = {0: str2date},comments='#')

#%%Create datasat with the "childmost" being an array with data taken from every year for a given day of the month
WIND_stats = [getsubdata(WIND,i,2) for i in np.arange(12)+1] #at 12pm
TEMP_stats = [getsubdata(TEMP,i,2) for i in np.arange(12)+1] #at 12pm
RAIN_stats = [getsubdata(RAIN,i,2) for i in np.arange(12)+1] #at 12pm
CLOU_stats = [getsubdata(CLOU,i,2) for i in np.arange(12)+1] #at 12pm
   
#%% Plot
monthlbl = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
days = np.arange(1,32)

makeplot(WIND_stats,40,'Wind speed','Mean Wind speed (knots)','Day in month at 12PM')
makeplot(TEMP_stats,35,'Temperature','Mean Temperature (°C)','Day in month at 12PM')
makeplot(RAIN_stats,4.5,'Rain','Mean Rain (mm/hour)','Day in month at 12PM')
makeplot(CLOU_stats,100,'Cloud cover','Mean Cloud cover (%)','Day in month at 12PM')