# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 23:08:19 2020
@author: Ivan
"""
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# Data taken from https://www.worldometers.info/coronavirus/
total_cases =   np.array([845, 1317, 2015, 2800, 4581, 6058, 7813, 9821, 11948, 14551, 17389, 20628, 24553, 28276, 31439, 34876, 37552, 40553, 43099, 45170])
daily_cases = np.array([265,  472,  698,  785, 1781, 1477, 1755, 2008,  2127,  2603,  2838,  3239,  3925,  3723,  3163,  3437,  2676,  3001,  2546,  2071])
dead_cases =  np.array([0  ,    0,   15,   24,   26,   26,   38,   43,    46,    45,    58,    64,    66,    73,    73,    86,    89,    97,   108,    97]) #1st two points are made up
closed_cases = dead_cases/0.03 #Divide by fatality rate to get total closed cases

# Define functions
def Infection_model_mode(t_in,t0,t_close,r0,K,mode):
    """
    t_in     : time at which to calculate [day]
    t0       : time at which infections started [day]
    t_close  : time until no longer infectious (closed case) [day]
    r0       : initial infection rate constant [/day]
    K        : maximum possible total number of cases (or carrying capacity)
    """
    # Model Parameters
    dt = 1/400 #Time step (Smaller is more accurate) [days]
    P0 = 1 #Initial infected population (always starts at 1)
    t_a = np.arange(0,t_in.max()+t0,dt) #Time range to calculate [days]

    # Define initial conditions and lists
    P, dPdt = ([P0],[0])
    P_new_list, P_closed_list = ([0],[0])
    P_total_cases_list = [P0]
    if mode: delta_ind = int(t_close // dt + 1) #So only calculates once if mode==True
    
    # Calculate
    for ind,t in enumerate(t_a): #For each time
        r = r0*(1-P_total_cases_list[-1]/K) #Infection rate constant (q used as "carrying capacity") [/day]
        dP_new = r*P[-1] #rate of new infected cases [/day]
        if mode: #If mode==True use the fast calculation otherwise linear interpolation
            dP_closed = P_new_list[-delta_ind] if t >= t_close else 0 #rate of closed cases [/day]
        else:
            dP_closed = np.interp(t-t_close,t_a[:ind+1],P_new_list) if t >= t_close else 0 #rate of closed cases [/day]
        P_total_cases = P_total_cases_list[-1]+dt*dP_new #Current number of total cases
        
        #Numerical difference time stepping
        dPdt_curr = dP_new - dP_closed  #Change in population for current step [/days]
        P_curr = P[-1] + dt*dPdt[-1] #Population for current step (forward Euler method)
            
        #Append arrays
        P.append(P_curr)
        P_total_cases_list.append(P_total_cases)
        dPdt.append(dPdt_curr)
        P_new_list.append(dP_new)
        P_closed_list.append(dP_closed)
        
    t_a = np.append(t_a,t_a[-1]+dt) #Include the time for the last calculated point as well
    return P_new_list, P_closed_list, P_total_cases_list, t_a

def Infection_model_fit(t_in,t0,t_close,r0,K):
    P_new_list, P_closed_list, P_total_cases_list, t_a = Infection_model(t_in,t0,t_close,r0,K)
    #Interpolate to get points exactly at time t_in
    P_total_cases_list = np.interp(t_in+t0,t_a,P_total_cases_list)
    P_new_list = np.interp(t_in+t0,t_a,P_new_list)
    P_closed_list = np.interp(t_in+t0,t_a,P_closed_list)
    return np.append(P_total_cases_list,np.append(P_new_list,P_closed_list)) #Three arrays appended into one for fitting


#%% Non-linear least squares fitting
Infection_model = lambda t_in,t0,t_close,r0,K : Infection_model_mode(t_in,t0,t_close,r0,K,False) #Interp version for fitting
day = np.arange(0,len(total_cases)) #Time [day]
pguess = [20,5,0.4,6e4]
popt, pcov = curve_fit(Infection_model_fit, day, np.append(np.append(total_cases,daily_cases),closed_cases), pguess)
perr = np.sqrt(np.diag(pcov)) #compute one standard deviation errors on the parameters

#%% Plot the data and its fit curve
Infection_model_fast = lambda t_in,t0,t_close,r0,K : Infection_model_mode(t_in,t0,t_close,r0,K,True) #Faster version for plotting

plt.figure()
plt.plot(day,total_cases,'ko')
plt.plot(day,daily_cases,'ro')
plt.plot(day,closed_cases,'go')

t0_fit = popt[0]
tau_fit = popt[1]

day_ext = np.linspace(-t0_fit,3*len(total_cases))
Pna, Pra, totca, t_a = Infection_model_fast(day_ext,*popt)
plt.plot(t_a-t0_fit,totca,'k-')
plt.plot(t_a-t0_fit,Pna,'r-')
plt.plot(t_a-t0_fit,Pra,'g-')

plt.xlabel("Time (days)")
plt.ylabel("Number of people")
plt.legend(["Total cases, $P_{total}$",
            "New cases, $P_{new}$",
            "Closed cases, $P_{closed}$"])

#%% Plot the data with curves sampled from the multivariate normal distribution of the fitted parameters
fig,(ax1,ax2,ax3) = plt.subplots(3,1,sharex=True)
ax1.plot(day,total_cases,'ko')
ax2.plot(day,daily_cases,'ro')
ax3.plot(day,closed_cases,'go')

t0_fit = popt[0]
tau_fit = popt[1]

ax1.set_ylabel("$P_{total}$")
ax2.set_ylabel("$P_{new}$")
ax3.set_ylabel("$P_{closed}$")
ax3.set_xlabel("Time (days)")

skip = 300 #larger number reduces plotted points for faster plotting
alpha=0.01 #smaller number makes the curves more transparent
for i in range(300):
    prand = np.random.multivariate_normal(mean=popt,cov=pcov) #Draw random samples from a multivariate normal distribution
    t0_fit = prand[0]
    day_ext = np.linspace(-t0_fit,3*len(total_cases))
    Pna, Pra, totca, t_a = Infection_model_fast(day_ext,*prand)
    time = t_a-t0_fit
    ax1.plot(time[::skip],totca[::skip],'k-',alpha=alpha)
    ax2.plot(time[::skip],Pna[::skip],'r-',alpha=alpha)
    ax3.plot(time[::skip],Pra[::skip],'g-',alpha=alpha) 
