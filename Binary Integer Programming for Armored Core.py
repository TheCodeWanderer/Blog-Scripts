# -*- coding: utf-8 -*-
"""
Optimize some objective function for a build in Armored Core Last Raven

In the data energy weapon attack values are increased by 6.9% assuming the use of the optional part O04-GOLGI

Mobility is calculated correctly when not using tune mode... but with tune mode it is underestimated

Created on Sat Mar 18 22:55:00 2023

@author: CodeWanderer
"""
import numpy as np
import cvxpy as cp
import pandas as pd
import time

useSCIP = 0 #use SCIP solver; faster depending on problem (!! available on "conda activate scip")
ninebreaker = 0 #Consider only the parts from ninebreaker
tune = 1 #apply tuning (slower)
defOP = 1 #Use 10% increase for SD and ED from optional part (O01-ANIMO, CR-O69ES)
encapOP = 1 #Increase condensor capacity optional part, adds 8000 to EN CAP (CR-O71EC)
coolOP = 1 #Increase cooling performance optional part (MARISHI), 5% increase from total cooling of exterior parts (excluding radiator)

#%%
def GroundBoostSpeed(BoostPower,totalWeight):
    """ Calculates the ground boost speed from boost power and total weight.
    The total weight contribution is capped to no less than 4797.
    The aerial boost speed is just GroundBoostSpeed*0.7764282860913.
    """
    if totalWeight<=4797:
        gweight=4797
    else:
        gweight=totalWeight
    return BoostPower*(106.4/(gweight)+0.00483) #BoostPower*0.027 when totalWeight<=4797
    # return BoostPower*(106.4/totalWeight+0.00483)

def SolidDamageRate(defs,AP,OP):
    """ Calculates the reduced damage rate (per thousand) due to solid defence """
    if OP: defs = np.floor( defs * 1.15 ) #if using ANIME optional part increase by 15%
    defs_k = np.ceil((3267-defs)/50) #"damage factor" (lower is better)
    if ( defs_k > 45 ): defs_k = 45 #--this value can not exceed 45
    # hp_s = np.floor(AP * 106.75 / defs_k) #"Entire durability"
    dams = np.round(  10000 * defs_k / 106.75 ) / 10 #Damage rate (out of 1000; lower is better)
    return dams

def cp_SolidDamageRate(defs,AP,OP): #modified!
    """ Calculates the reduced damage rate (per thousand) due to solid defence """
    if OP: defs = cp.floor( defs * 1.15 ) #if using ANIME optional part increase by 15%
    defs_k = cp.ceil((3267-defs)/50) #"damage factor"
    # defs_k = cp.min(cp.hstack([defs_k, 45])) #--this value can not exceed 45
    dams = 1000 * defs_k / 106.75 #Damage rate (out of 1000; lower is better)
    return dams

def EnergyDamageRate(defe,AP,OP):
    """ Calculates the reduced damage rate (per thousand) due to energy defence """
    if OP: defe = np.floor( defe * 1.15 ) #If using CR-O69ES optional part increase by 15%
    defe_k = np.ceil((3205-defe)/50)
    if ( defe_k > 45 ): defe_k = 45
    # hp_e = np.floor(AP * 106.75 / defe_k)
    dame = np.round(  10000 * defe_k / 106.75 ) / 10
    return dame

def cp_EnergyDamageRate(defe,AP,OP): #modified!
    """ Calculates the reduced damage rate (per thousand) due to energy defence """
    if OP: defe = cp.floor( defe * 1.15 ) #If using CR-O69ES optional part increase by 15%
    defe_k = cp.ceil((3205-defe)/50)
    # if ( defe_k > 45 ): defe_k = 45
    dame = 1000 * defe_k / 106.75
    return dame
    
def cleanNaNPSP(df):
    df.PSP = df.PSP.fillna(False) if "PSP" in df else None #does not need a return because accessing object directly

def removePSP(df): #Remove parts from Last Raven Portable
    return df.drop(np.argwhere(df.PSP.to_numpy()).flatten()) if "PSP" in df else df

# def removeLR(df): #Remove parts from Last Raven PS2 (leaves with Ninebreaker parts)
#     return df.drop([13,24])

def subpart(df,label):
    """ label should be like r'ARM EITHER|ARM LEFT' """
    return Part('',dataframe=weapon.data[weapon.data['SLOT'].str.contains(label)].reset_index(drop=True))
    #return Part('',dataframe=df.drop(np.where(weapon.data.SLOT != label)[0]).reset_index(drop=True))

def multsum(x,y):
    return cp.sum(cp.multiply(x, y))

def getrank(cat,val):
    out = lambda v1,v2 : "S" if val >= v1 else ("A" if val >= v2 else "<A")
    if cat == "DEF": return out(4000,3800)
    if cat == "MOB": return out(480,410) #MOBILITY
    if cat == "ENSUP": return out(10400,9800) #ENERGY SUPPLY VALUE (SUP + CAP/10)
    if cat == "ATK": return out(25000,20000)
    if cat == "COOLING": return out(35000,34000)
    if cat == "VSECM": return out(1000,820) # VS ECM
    
# tuning functions for weight
def tune_head_weight(tune,start_weight):
    """ approximate relation for tuned weight """
    slope = 8.61e-4*tune**2 - 2.37e-2*tune + 1
    constant = -0.0495*tune**2 + 1.2362*tune
    return slope*start_weight + constant

def tune_core_weight(tune,start_weight):
    """ approximate relation for tuned weight """
    slope = 6.02e-4*tune**2 - 1.60e-2*tune + 1
    constant = -0.3366*tune**2 + 8.3484*tune
    return slope*start_weight + constant

def tune_arm_weight(tune,start_weight):
    """ approximate relation for tuned weight """
    slope = 2.90e-4*tune**2 - 7.97e-3*tune + 1
    constant = -0.0471*tune**2 + 1.0333*tune
    return slope*start_weight + constant

def tune_leg_weight(tune,start_weight):
    """ approximate relation for tuned weight """
    slope = 5.79e-4*tune**2 - 1.58e-2*tune + 1
    constant = -0.7476*tune**2 + 20.043*tune
    return slope*start_weight + constant

def tune_leg_maxlegweight(tune,start_weight):
    """ approximate relation for tuned max leg weight """
    slope = 3.522e-4*tune**2 - 8.715e-3*tune + 1
    constant = -3.1483*tune**2 + 82.488*tune
    return slope*start_weight + constant

# tuning functions for shell defense
def tune_head_shelldef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 8.56e-4*tune**2 - 2.41e-2*tune + 1
    constant = -0.2433*tune**2 + 7.0168*tune
    return slope*start_weight + constant

def tune_core_shelldef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 4.02e-4*tune**2 - 1.10e-2*tune + 1
    constant = -0.3035*tune**2 + 8.5788*tune
    return slope*start_weight + constant

def tune_arm_shelldef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 4.54e-4*tune**2 - 1.25e-2*tune + 1
    constant = -0.2896*tune**2 + 8.1174*tune
    return slope*start_weight + constant

def tune_leg_shelldef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 3.72e-4*tune**2 - 1.08e-2*tune + 1
    constant = -0.3608*tune**2 + 10.599*tune
    return slope*start_weight + constant

# tuning functions for energy defense
def tune_head_energydef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 8.53e-4*tune**2 - 2.40e-2*tune + 1
    constant = -0.2301*tune**2 + 6.9124*tune
    return slope*start_weight + constant

def tune_core_energydef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 4.87e-4*tune**2 - 1.13e-2*tune + 1
    constant = -0.3336*tune**2 + 8.6794*tune
    return slope*start_weight + constant

def tune_arm_energydef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 4.52e-4*tune**2 - 1.24e-2*tune + 1
    constant = -0.2793*tune**2 + 7.9551*tune
    return slope*start_weight + constant

def tune_leg_energydef(tune,start_weight):
    """ approximate relation for tuned shell defense """
    slope = 3.97e-4*tune**2 - 1.11e-2*tune + 1
    constant = -0.3500*tune**2 + 9.8285*tune
    return slope*start_weight + constant

def w2tune(w):
    """ Convert the solution to the encoding boolean array to the x and y array """
    W=np.round(w.value)
    index = np.argwhere(W==1)
    # x = W[index[0][0],:].astype(bool) #solution for the x boolean array
    tune = W[:,index[0][1]].astype(bool) #solution for the y boolean array
    return tune

#%% OBJECT
from typing import List

class Part:
    # def __init__(self, filename: str, col_names: List[str], drop_list: List[int] = [], clean: bool = True):
    def __init__(self, filename: str, drop_list: List[int] = [], dataframe: pd.DataFrame = None):
        if dataframe is not None:
            self.data = dataframe.copy()
        else:
            self.filename = filename
            # self.col_names = col_names
            self.drop_list = drop_list #remove specified parts by index
            # self.clean = clean
            self.read_data() #read data from text file and import as pandas
        self.bool = cp.Variable(len(self.data), boolean=True) #create cvxpy boolean array to solve for which part is selected

    def read_data(self):
        with open(self.filename, "r") as f:
            self.data = pd.read_csv(f, sep='\t', thousands=",")#, usecols=self.col_names)
            cleanNaNPSP(self.data)
            self.data = removePSP(self.data)
            if self.drop_list:
                self.data = self.data.drop(self.drop_list)
            self.data = self.data.reset_index(drop=True)
            self.nan2zero()
    
    def nan2zero(self): #set all nan to zero
        self.data.fillna(0, inplace=True)
        
    def get_sol(self): #get part name from solution
        if np.sum(np.round(self.bool.value))==0:
            return "unequipped"
        else:
            return self.data["NAME"][getind(self.bool.value)].values[0]
        
    def get_col(self, col_name: str):
        return self.data[col_name].to_numpy()

    def WEIGHT(self):
        return self.get_col("WEIGHT")

    def AP(self):
        return self.get_col("ARMOR POINTS")

    def DS(self):
        return self.get_col("DEF SHELL")

    def DE(self):
        return self.get_col("DEF ENERGY")
    
    def COOLING(self):
        return self.get_col("COOLING")
    
    def FCOOLING(self):
        return self.get_col("FORCED COOLING")
    
    def VSECM(self):
        return self.get_col("VS ECM")
    
    def ENOUT(self):
        return self.get_col("ENERGY OUTPUT")
    
    def CONDCAP(self):
        return self.get_col("CONDENSER CAPACITY")
    
    def EMRGCAP(self):
        return self.get_col("EMERGENCY CAPACITY")
    
    def ENDRAIN(self):
        try:
            return self.get_col("ENERGY DRAIN")
        except:
            return self.get_col("MOVING DRAIN") #EN SUP determined by this rather than stationary drain
    
    def MLW(self):
        return self.get_col("MAX LEG WEIGHT")
    
    def MAW(self):
        return self.get_col("MAX ARM WEIGHT")
    
    def BP(self):
        return self.get_col("BOOST POWER")
    
    def SLOTS(self):
        return self.get_col("SLOTS")
    
    def OS(self):
        return self.get_col("OPTION SLOTS")
    
    def TFP(self): #total firepower
        return self.get_col("FIREPOWER")
        # arr = self.get_col("TOTAL FIREPOWER")
        # return self.get_col("TOTAL FIREPOWER") #solves immediately!
        # return (self.get_col("ATTACK POWER")*self.get_col("AMMO COUNT"))/10 #takes forever to solve!
    
#%%Load data
head = Part("ACLR_Head.tsv", [13,24,1,7,14] if ninebreaker else [])

core = Part("ACLR_Core.tsv", [20,19,18,10,8] if ninebreaker else [])
core.data["FIREPOWER"] = core.data["ATTACK POWER"]*core.data["EO AMMO COUNT"] #make new column refering to the firepower

arm = Part("ACLR_Arm.tsv")

leg = Part("ACLR_Leg.tsv")

boost = Part("ACLR_Booster.tsv")
# optional = Part("ACLR_OptionalPart.tsv")
generator = Part("ACLR_Generator.tsv")
radiator = Part("ACLR_Radiator.tsv")
fcs = Part("ACLR_FCS.tsv")

weapon = Part("ACLR_Weapon.tsv") #In the data energy weapon attack values are increased by 6.9% assuming the use of the optional part O04-GOLGI
weapon.data["FIREPOWER"] = weapon.data["ATTACK POWER"]*weapon.data["AMMO COUNT"] #make new column refering to the firepower

backECM = Part("ACLR_Back.tsv")
backECM.data = backECM.data[pd.Index(["NAME","WEIGHT","ENERGY DRAIN","VS ECM"])]

armL = subpart(weapon,r'ARM EITHER|ARM LEFT') #Part('',dataframe=weapon.data[weapon.data['SLOT'].str.contains(r'ARM EITHER|ARM LEFT')].reset_index(drop=True))
# armL.TFP()[np.isinf(armL.TFP())]=0

armR = subpart(weapon,r'ARM EITHER|ARM RIGHT') #Part('',dataframe=weapon.data[weapon.data['SLOT'].str.contains(r'ARM EITHER|ARM RIGHT')].reset_index(drop=True))
# armR.TFP()[np.isinf(armR.TFP())]=0

armBoth = subpart(weapon,r'ARMS') #Weapon arms!

backL = subpart(weapon.data,r"BACK")
backR = subpart(weapon.data,r"BACK")
backL.data = pd.concat([backL.data, backECM.data]).fillna(0).reset_index(drop=True)
backR.data = pd.concat([backR.data, backECM.data]).fillna(0).reset_index(drop=True)
backL.bool = cp.Variable(len(backL.data), boolean=True)
backR.bool = cp.Variable(len(backR.data), boolean=True)

backBoth = subpart(weapon.data,"BACK BOTH")

extn = Part("ACLR_Extension.tsv")
extn.data["FIREPOWER"] = extn.data["ATTACK POWER"]*extn.data["AMMO COUNT"] #make new column refering to the firepower

inside = Part("ACLR_Inside.tsv")
inside.data["FIREPOWER"] = inside.data["ATTACK POWER"]*inside.data["AMMO COUNT"] #make new column refering to the firepower

#%% Pre-calc for tune
if tune:
    make2D = lambda arr, tunefunc : cp.Constant(np.asarray([tunefunc(i,arr) for i in range (11)])) #make 2D matrix of all the possible tuned values
    #2D matrix of all the possible weight and the tuned weight
    #--weights
    HWM = make2D(head.WEIGHT(),tune_head_weight) 
    CWM = make2D(core.WEIGHT(),tune_core_weight)
    AWM = make2D(arm.WEIGHT(),tune_arm_weight)
    LWM = make2D(leg.WEIGHT(),tune_leg_weight)
    #--shell defence
    HSDM = make2D(head.DS(),tune_head_shelldef) 
    CSDM = make2D(core.DS(),tune_core_shelldef)
    ASDM = make2D(arm.DS(),tune_arm_shelldef)
    LSDM = make2D(leg.DS(),tune_leg_shelldef)
    #--energy defence
    HEDM = make2D(head.DE(),tune_head_energydef) 
    CEDM = make2D(core.DE(),tune_core_energydef)
    AEDM = make2D(arm.DE(),tune_arm_energydef)
    LEDM = make2D(leg.DE(),tune_leg_energydef)

#%% Construct a CVXPY problem
if tune:
    #2D variable that selects one of all the possible tuned values
    #--weights
    headW_st = cp.Variable(HWM.shape, boolean=True) #encodes selection and tune boolean array into single array
    coreW_st = cp.Variable(CWM.shape, boolean=True) 
    armW_st = cp.Variable(AWM.shape, boolean=True) 
    legW_st = cp.Variable(LWM.shape, boolean=True)
    #--shell defence
    headSD_st = cp.Variable(HSDM.shape, boolean=True) #encodes selection and tune boolean array into single array
    coreSD_st = cp.Variable(CSDM.shape, boolean=True) 
    armSD_st = cp.Variable(ASDM.shape, boolean=True) 
    legSD_st = cp.Variable(LSDM.shape, boolean=True)
    #--energy defence
    headED_st = cp.Variable(HEDM.shape, boolean=True) #encodes selection and tune boolean array into single array
    coreED_st = cp.Variable(CEDM.shape, boolean=True) 
    armED_st = cp.Variable(AEDM.shape, boolean=True) 
    legED_st = cp.Variable(LEDM.shape, boolean=True)
      
#------parameters
totalAP = head.AP() @ head.bool + core.AP() @ core.bool + arm.AP() @ arm.bool + armBoth.AP() @ armBoth.bool + leg.AP() @ leg.bool #Total AP
reqWeight = boost.WEIGHT() @ boost.bool + generator.WEIGHT() @ generator.bool + radiator.WEIGHT() @ radiator.bool + fcs.WEIGHT() @ fcs.bool #other required parts
armweaponWeight = armL.WEIGHT() @ armL.bool + armR.WEIGHT() @ armR.bool #weapon weight

if tune:
    ArmWeight = multsum(AWM,armW_st) + armweaponWeight + extn.WEIGHT() @ extn.bool + inside.WEIGHT() @ inside.bool + armBoth.WEIGHT() @ armBoth.bool #L and R weapon
    frameWeight = multsum(HWM, headW_st) + multsum(CWM, coreW_st) + ArmWeight #weight of the frame only
    carryWeight = frameWeight + reqWeight + backL.WEIGHT() @ backL.bool + backR.WEIGHT() @ backR.bool + backBoth.WEIGHT() @ backBoth.bool #total weight carried by legs
    totalWeight = carryWeight + multsum(LWM, legW_st) #Total weight overall
    totalDS = multsum(HSDM, headSD_st) + multsum(CSDM, coreSD_st) + multsum(ASDM, armSD_st) + multsum(LSDM, legSD_st) + extn.DS() @ extn.bool + armBoth.DS() @ armBoth.bool #Total shell defense
    totalDE = multsum(HEDM, headED_st) + multsum(CEDM, coreED_st) + multsum(AEDM, armED_st) + multsum(LEDM, legED_st) + extn.DE() @ extn.bool + armBoth.DE() @ armBoth.bool #Total energy defense
else:
    ArmWeight = arm.WEIGHT() @ arm.bool + armweaponWeight + extn.WEIGHT() @ extn.bool + inside.WEIGHT() @ inside.bool + armBoth.WEIGHT() @ armBoth.bool #L and R weapon
    frameWeight = head.WEIGHT() @ head.bool + core.WEIGHT() @ core.bool + ArmWeight #weight of the frame only
    carryWeight = frameWeight + reqWeight + backL.WEIGHT() @ backL.bool + backR.WEIGHT() @ backR.bool + backBoth.WEIGHT() @ backBoth.bool#total weight carried by legs
    totalWeight = carryWeight + leg.WEIGHT() @ leg.bool #Total weight overall
    totalDS = head.DS() @ head.bool + core.DS() @ core.bool + arm.DS() @ arm.bool + leg.DS() @ leg.bool + extn.DS() @ extn.bool + armBoth.DS() @ armBoth.bool #Total shell defense
    totalDE = head.DE() @ head.bool + core.DE() @ core.bool + arm.DE() @ arm.bool + leg.DE() @ leg.bool + extn.DE() @ extn.bool + armBoth.DE() @ armBoth.bool #Total energy defense

sumDEF = (totalDE + totalDS)*(1 + defOP*0.10) #total defense

partscooling = head.COOLING() @ head.bool + core.COOLING() @ core.bool + arm.COOLING() @ arm.bool + armBoth.COOLING() @ armBoth.bool + leg.COOLING() @ leg.bool
cooling =  partscooling*(1 + coolOP*0.05) + radiator.COOLING() @ radiator.bool #normal cooling
forcedcooling = partscooling + radiator.FCOOLING() @ radiator.bool #forced cooling (parts cooling value determines the forced cooling value as well)
totcooling = cooling + forcedcooling #total cooling which determines the rank

ensup = generator.ENOUT() @ generator.bool - head.ENDRAIN() @ head.bool \
        - core.ENDRAIN() @ core.bool - arm.ENDRAIN() @ arm.bool - armBoth.ENDRAIN() @ armBoth.bool\
        - leg.ENDRAIN() @ leg.bool - boost.ENDRAIN() @ boost.bool \
        - fcs.ENDRAIN() @ fcs.bool - radiator.ENDRAIN() @ radiator.bool \
        - armL.ENDRAIN() @ armL.bool - armR.ENDRAIN() @ armR.bool \
        - backL.ENDRAIN() @ backL.bool - backR.ENDRAIN() @ backR.bool - backBoth.ENDRAIN() @ backBoth.bool \
        - extn.ENDRAIN() @ extn.bool - inside.ENDRAIN() @ inside.bool

encap = (generator.CONDCAP() + generator.EMRGCAP()*3) @ generator.bool + encapOP*8000 #Equation for determining the energy capacity stat
enrankval = ensup + encap/10 #ENERGY SUPPLY RANK VALUE (EN SUP + EN CAP/10) to determine rank  

vsecm = head.VSECM() @ head.bool + fcs.VSECM() @ fcs.bool + backL.VSECM() @ backL.bool + backR.VSECM() @ backR.bool #vs ECM

totFP = armL.TFP() @ armL.bool + armR.TFP() @ armR.bool + armBoth.TFP() @ armBoth.bool \
        + backL.TFP() @ backL.bool + backR.TFP() @ backR.bool + backBoth.TFP() @ backBoth.bool \
        + core.TFP() @ core.bool + extn.TFP() @ extn.bool + inside.TFP() @ inside.bool 

boostBP = boost.BP() @ boost.bool + leg.BP() @ leg.bool

#------The objective function is to maximize the total AP
# ~~maximizers~~
# objective = cp.Maximize(totalAP)
# objective = cp.Maximize(totalWeight)
# objective = cp.Maximize(totalDS)
# objective = cp.Maximize(totalDE)

# objective = cp.Maximize(totFP)
# objective = cp.Maximize(sumDEF)
# objective = cp.Maximize(boostBP)
# objective = cp.Maximize(ensup)
# objective = cp.Maximize(enrankval)
# objective = cp.Maximize(totcooling)
# objective = cp.Maximize(vsecm)

# objective = cp.Maximize(vsecm + totcooling + ensup + boostBP + sumDEF + totFP)
# objective = cp.Maximize(vsecm/784 + totcooling/16087 + ensup/10188 + boostBP*0.027/678 + sumDEF/3942 + totFP/66108)
# objective = cp.Maximize(vsecm/1000 + totcooling/35000 + ensup/2200 + boostBP*0.027/480 + sumDEF/4000 + totFP/250000)
 
#~~minimizers~~
# objective = cp.Minimize(totalWeight) #<-- for optimizing mobility
# objective = cp.Minimize(ensup)
# objective = cp.Minimize(cp_SolidDamageRate(totalDS,totalAP,False)) #gives same as max totalDS
# objective = cp.Minimize(cp_EnergyDamageRate(totalDE,totalAP,False)) #gives same as max totalDE

#*dqcp objectives*
objective = cp.Maximize(boostBP/totalWeight) #<-- for optimizing mobility, i.e. max boost speed
# objective = cp.Maximize((10*boostBP+sumDEF)/totalWeight) #<-- for optimizing mobility and defense
# objective = cp.Maximize(sumDEF*totalAP)
# objective = cp.Maximize(totalAP/totalWeight) #! Requires qcp=True
# objective = cp.Maximize(totalDS/totalWeight)
# objective = cp.Maximize(totalDE/totalWeight)
# objective = cp.Maximize(sumDEF/totalWeight)
# objective = cp.Maximize(totalDS*totalAP) #gives same as maximize(totalDS)
# objective = cp.Maximize(totalDE*totalAP) #gives different (and better?) than maximize(totalDE)
# objective = cp.Maximize(totFP/totalWeight)

#~~failed~~
# objective = cp.Maximize(GroundBoostSpeed(boostBP @ boost.bool, totalWeight)) #not DCP
# objective = cp.Maximize(cp.multiply(106.4/4797+0.00483, boostBP @ boost.bool)) #not DCP
# objective = cp.Maximize(106.4*(boostBP @ boost.bool)/totalWeight) + cp.Maximize(boostBP @ boost.bool) #not DCP
 
#-----The constraint is the the total weight of all parts should not exceed max leg weight of the chosen leg
LegConstr = carryWeight <= leg.MLW() @ leg.bool #not to exceed max leg weight
CoreConstr = ArmWeight <= core.MAW() @ core.bool #not to exceed max arm weight of core

#Boolean constraints (only 1 part can be selected)
constraints = [cp.sum(head.bool)==1, #only 1 head part
               cp.sum(core.bool)==1, #only 1 core part
               cp.sum(arm.bool) + cp.sum(armBoth.bool) == 1, #only 1 arm part or 1 weapon arm part
               cp.sum(leg.bool)==1, #only 1 leg part
               cp.sum(boost.bool) + (leg.BP()>0) @ leg.bool == 1, #ensures either leg with boosters or external boosters
               cp.sum(generator.bool)==1,
               cp.sum(radiator.bool)==1,
               cp.sum(fcs.bool)==1,
               ensup>=0]

constraints += [cp.sum(armL.bool) + cp.sum(armBoth.bool) <= 1, #parts can be unequipped hence the <, also can not equip if using weapon arms
                cp.sum(armR.bool) + cp.sum(armBoth.bool) <= 1,
                cp.sum(backL.bool) + cp.sum(backBoth.bool) <= 1, #back can have a single or double back part
                cp.sum(backR.bool) + cp.sum(backBoth.bool) <= 1,
                cp.sum(extn.bool)<=1,
                cp.sum(inside.bool)<=1] 

#--Weight constraints
constraints += [LegConstr, 
               CoreConstr]

if tune:
    #The 2D arrays also require a total value of 1
    #--weights
    constraints += [cp.sum(headW_st)==1,
                    cp.sum(coreW_st)==1,
                    cp.sum(armW_st)==1,
                    cp.sum(legW_st)==1]
    #--shell defence
    constraints += [cp.sum(headSD_st)==1,
                    cp.sum(coreSD_st)==1,
                    cp.sum(armSD_st)==1,
                    cp.sum(legSD_st)==1]
    #--shell defence
    constraints += [cp.sum(headED_st)==1,
                    cp.sum(coreED_st)==1,
                    cp.sum(armED_st)==1,
                    cp.sum(legED_st)==1]
    #The selection arrays have to match the selected part from the 2D tune array
    #--weights
    constraints += [head.bool==cp.sum(headW_st,axis=0),
                    core.bool==cp.sum(coreW_st,axis=0),
                    arm.bool==cp.sum(armW_st,axis=0),
                    leg.bool==cp.sum(legW_st,axis=0)]
    #--shell defence
    constraints += [head.bool==cp.sum(headSD_st,axis=0),
                    core.bool==cp.sum(coreSD_st,axis=0),
                    arm.bool==cp.sum(armSD_st,axis=0),
                    leg.bool==cp.sum(legSD_st,axis=0)]
    #--energy defence
    constraints += [head.bool==cp.sum(headED_st,axis=0),
                    core.bool==cp.sum(coreED_st,axis=0),
                    arm.bool==cp.sum(armED_st,axis=0),
                    leg.bool==cp.sum(legED_st,axis=0)]
    #Total tune value for one part across categories must be no more than 10
    T=np.arange(11,dtype=int)
    sum1 = lambda x : cp.sum(x,axis=1)
    constraints += [T @ (sum1(headW_st) + sum1(headSD_st) + sum1(headED_st)) <= 10,
                    T @ (sum1(coreW_st) + sum1(coreSD_st) + sum1(coreED_st)) <= 10,
                    T @ (sum1(armW_st) + sum1(armSD_st) + sum1(armED_st)) <= 10,
                    T @ (sum1(legW_st) + sum1(legSD_st) + sum1(legED_st)) <= 10]
# if useSlots:
#     SlotConstr = totalSlot <= core.OS() @ core.bool #not to exceed slot capacity of core
#     constraints += [SlotConstr]

#Special constrains for ensuring that the build satisfies a minimum rank for some performance categories
constraints += [totFP>=250000] #S rank firepower
constraints += [enrankval>=10400] #S rank energy supply
constraints += [totcooling>=35000] #S rank cooling
constraints += [sumDEF>=4000] #S rank defence
constraints += [vsecm>=1000] #S rank vs ecm

# constraints += [totFP>=200000] #A rank firepower
# constraints += [enrankval>=9800] #A rank energy supply
# constraints += [sumDEF>=3800] #A rank defence
# constraints += [vsecm>=820] #S rank vs ecm
#%% Solve the problem
prob = cp.Problem(objective, constraints)

start_time = time.time()
if useSCIP:
    prob.solve(solver="SCIP",qcp=(prob.is_dqcp() if not prob.is_dcp() else False))#,verbose=True)
else:
    prob.solve(qcp=(prob.is_dqcp() if not prob.is_dcp() else False))
end_time = time.time()
print("Time Elapsed:",end_time-start_time,"s")

#%% Display results
a2int = lambda arr : np.array(np.round(arr.value),dtype="int") #convert solution to int array
# getind = lambda x : np.argwhere(x==1)[0] #get index of solution
getind = lambda x : np.argwhere(np.round(x)==1)[0] #get index of solution

if tune:
    #--weights
    headW_tune = w2tune(headW_st)
    coreW_tune = w2tune(coreW_st)
    armW_tune = w2tune(armW_st)
    legW_tune = w2tune(legW_st)
    #--shell defence
    headSD_tune = w2tune(headSD_st)
    coreSD_tune = w2tune(coreSD_st)
    armSD_tune = w2tune(armSD_st)
    legSD_tune = w2tune(legSD_st)
    #--energy defence
    headED_tune = w2tune(headED_st)
    coreED_tune = w2tune(coreED_st)
    armED_tune = w2tune(armED_st)
    legED_tune = w2tune(legED_st)

#Get rank of AC
boostval = GroundBoostSpeed(boostBP.value, totalWeight.value)
TOTFP = totFP/10 #total firepower

ATK_rank = getrank("ATK",TOTFP.value)
DEF_rank = getrank("DEF",sumDEF.value)
MOB_rank = getrank("MOB",boostval)
EN_rank = getrank("ENSUP",enrankval.value)
COOLING_rank = getrank("COOLING",totcooling.value)
VSECM_rank = getrank("VSECM",vsecm.value)

#%%    
print("Optimization status: ", prob.status)
print("The optimized value is:", prob.value)
print("============================")
print("Head:", head.get_sol(), f"[w:{T[headW_tune][0]}, SD:{T[headSD_tune][0]}, ED:{T[headED_tune][0]}]" if tune else "")
print("Core:", core.get_sol(), f"[w:{T[coreW_tune][0]}, SD:{T[coreSD_tune][0]}, ED:{T[coreED_tune][0]}]" if tune else "")
if sum(np.round(armBoth.bool.value))>0:
    print("Arm:", armBoth.get_sol())
else:
    print("Arm:", arm.get_sol(), f"[w:{T[armW_tune][0]}, SD:{T[armSD_tune][0]}, ED:{T[armED_tune][0]}]" if tune else "")
print("Leg:", leg.get_sol(), f"[w:{T[legW_tune][0]}, SD:{T[legSD_tune][0]}, ED:{T[legED_tune][0]}]" if tune else "")
print("Booster:", boost.get_sol())
print("FCS:", fcs.get_sol())
print("Generator:", generator.get_sol())
print("Radiator:", radiator.get_sol())
print("Inside:", inside.get_sol())
print("Extension:", extn.get_sol())
if sum(np.round(backBoth.bool.value))>0:
    print("Back Both:", backBoth.get_sol())
else:
    print("Back R:", backR.get_sol())
    print("Back L:", backL.get_sol())
if sum(np.round(armBoth.bool.value))==0:
    print("Arm R:", armR.get_sol())
    print("Arm L:", armL.get_sol())
print("============================")
print("Total AP:", int(np.round(totalAP.value)))
print("Total Shell Defense:", int(np.round(totalDS.value)))
print("-- reduction rate:", SolidDamageRate(totalDS.value,totalAP.value,False))
print("Total Energy Defense:", int(np.round(totalDE.value)))
print("-- reduction rate:", EnergyDamageRate(totalDE.value,totalAP.value,False))
print("Frame weight:", int(np.round(frameWeight.value)))
print("Total weight:", int(np.round(totalWeight.value)))
print("Carrying weight:", int(np.round(carryWeight.value)))
print("-- Max Leg Weight:", leg.MLW() @ leg.bool.value)
print("Ground Boost Speed:", round(boostval,1))
print("Energy Supply:", round(ensup.value))
print("Energy Capacity:", round(encap.value))
print("============================")
print("ATK:",round(TOTFP.value,1),f"({ATK_rank})")
print("DEF:",round(sumDEF.value,1),f"({DEF_rank})")
print("MOB:",round(boostval,1),f"({MOB_rank})")
print("EN SUP:",round(enrankval.value,1),f"({EN_rank})")
print("COOLING:",totcooling.value,f"({COOLING_rank})")
print("VS ECM:",round(vsecm.value,1),f"({VSECM_rank})")
print("============================")
if defOP: print("001-ANIMO & CR-069ES")
if encapOP: print("CR-O71EC")
if coolOP: print("MARISHI")
print("004-GOLGI")
print("AP/FrameWeight:",int(np.round(totalAP.value))/int(np.round(frameWeight.value)))
print("DS/FrameWeight:",int(np.round(totalDS.value))/int(np.round(frameWeight.value)))
print("DE/FrameWeight:",int(np.round(totalDE.value))/int(np.round(frameWeight.value)))
# print(tuneAW_int.value)
