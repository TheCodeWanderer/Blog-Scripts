# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 23:45:00 2019

@author: Ivan
"""
import numpy as np
import sys, csv, re
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.colors as colors
#%%########################	 User input #######################################

extended = True #Set boolean to True to use the digraphs in the analysis

#%%########################	Functions 	#######################################
def colorbar(mappable,pad):
    """ Makes a nice colorbar """
    a = mappable.axes
    f = a.figure
    divider = make_axes_locatable(a)
    ca = divider.append_axes("right", pad=pad, size="5%")
    return f.colorbar(mappable, cax=ca)

def isspecial(word):
    """ Retuns boolean if there is a special character in a string"""
    return False if re.match("^[a-zA-Z0-9_]*$", word) else True

def lett2num(character):
	""" Returns the ASCII order number of the character (after making it lowercase) """
    # a -> 0, ..., z -> 25
	return int(ord(character.lower()) - 97)

def num2lett(ind):
    """ Returns the alphabet string based on the order number """
    # 0 -> a, ..., 25 -> z
    return chr(ind + 97)
	  
def Words2Matrix(WordList):
	""" Converts a list of words to a matrix """
	#Size: words x length of alphabet (26)
	WordMatrix = np.zeros((len(WordList),26)) #cols is # of letters
	for ind, word in enumerate(WordList): #for each word
		for char in word:
			WordMatrix[ind,lett2num(char)] = int(1)
	return WordMatrix

def Words2MatrixEX(WordList):
    """ Converts a list of words to a matrix with extended alphabet set """
    #Size: words x length of alphabet + digraphs
    WordMatrix = np.zeros((len(WordList),26+len(digraphs))) #cols is # of letters
    for ind, word in enumerate(WordList): #For each word...
        for dbla in list(digraphs.keys()): #Find the digraphs first...
            if word.find(dbla)>-1:
                word = word.replace(dbla,'') #remove them from the word
                WordMatrix[ind,digraphs[dbla]] = int(1) #Make that part of the matrix equal to 1
        for char in word:
            WordMatrix[ind,lett2num(char)] = int(1)
    return WordMatrix

def Phones2Matrix(PhonemeList):
	""" Converts a phonemes of words to a matrix """
	#Size: words x length of phoneme alphabet (39)
	PhoneMatrix = np.zeros((len(PhonemeList),len(Phones))) #cols is # of letters
	for ind, PhonemeVec in enumerate(PhonemeList): #For each word
		for Phoneme in PhonemeVec: #for each phoneme in each word
			Phoneme = nodigits(Phoneme) #Removes the inflection #s
			PhoneMatrix[ind,Phones[Phoneme]-1] = int(1)
	return PhoneMatrix
	
def Word2OrderedMatrix(Word):
	""" Converts a word to a matrix; preserves character order """
	#Size: # of chars in word x length of alphabet (26)
	WordMatrix = np.zeros((len(Word),26)) #rows is # of letters in word
	for ind, char in enumerate(Word):
		WordMatrix[ind,lett2num(char)] = int(1)
	return WordMatrix

def Phone2OrderedMatrix(PhonemeVec):
	""" Converts a list of phonemes to a matrix; preserves Phoneme order """
	#Size: # of Phonemes in list x length of alphabet (26)
	PhoneMatrix = np.zeros((len(PhonemeVec),39)) #cols is # of letters
	for ind, Phoneme in enumerate(PhonemeVec): #For each word
		Phoneme = nodigits(Phoneme) #Removes the inflection #s
		PhoneMatrix[ind,Phones[Phoneme]-1] = int(1)
	return PhoneMatrix
		
def PhonemeVec2WordVec(PhonemeVec,invmap):
    """ Transform a list of phonemes to characters based on the correlation matrix"""
    OP = Phone2OrderedMatrix(PhonemeVec) #Matrix of phonemes
    Phone2Word = np.matmul(OP,invmap) #Matrix indicating the alphabet from the phonemes 
    LtLi = np.argmax(Phone2Word,axis=1) #likely phones
    if extended: #If using the digraph set as well
        digkeys = list(digraphs.keys())
        WV = []
        for ind in LtLi:
            if ind>25:
                WV.append(digkeys[ind-26]) #append a digraph
            else:
                WV.append(num2lett(ind)) #append a character
    else:
        WV = [num2lett(ind) for ind in LtLi]
    return WV

def Word2PhonemeVec(Word,map):
    """ Converts a word string to its phonemes """
    OM = Word2OrderedMatrix(Word)
    Word2Phone = np.matmul(OM,map)
    PhLi = np.argmax(Word2Phone,axis=1) #likely phones
    return [keys[ind] for ind in PhLi] #List of phoneme in the word
	
def GetWordList():
	""" Extract words into a list from a table of 5000 most frequently used English words """
    #!Top5000English.txt should be in the same directory as this file!
	with open(sys.path[0] + '\Top5000English.txt','r') as f:
		reader = csv.reader(f, delimiter='\t')
		next(reader) #Skip header row
		return [col2.strip() for col1, col2, col3, col4, col5 in reader]

def nodigits(s):
	""" Remove #s from the string """
	return ''.join([i for i in s if not i.isdigit()])
		
def GetPhonemeList(WordList):
    """ For each word in a list of words extract their phonemes from the CMUdict """
    #!cmudict-0.7b should be in the same directory as this file!
    WordList_c = WordList[:]
    PhonemeList = []
    with open(sys.path[0] + '\cmudict-0.7b','r') as fh:
        for line in fh: #Check the line
            for keyword in reversed(WordList_c): #Have to make it reversed so when an element is removed it doesn't "skip" the next element (since it gets shifted down)
                keyword_UW = keyword.upper() + ' ' #Make upper case because of dictionary format. Add space so it is a whole word.
                len_k = len(keyword_UW) #Length of the string
                if keyword_UW in line[0:len_k]:
                    WordList_c.remove(keyword) #Remove the word from checking once it has been found once (SPEED UP!)
                    PhonemeList.append(line[len_k+1:-1].split(' '))  #removes \n special character from string and separates phonemes into parts in a list
    return PhonemeList, WordList_c #WordList_c will show what words were not found

def MakePhonemeDict(WordList):
    """ Makes a dictionary structure between the alphabetic word and its Phonemes"""
    WordList_c = WordList[:]
    PhonemeDict = {}
    with open(sys.path[0] + '\cmudict-0.7b','r') as fh:
        for line in fh: #Check the line
            for keyword in reversed(WordList_c): #Have to make it reversed so when an element is removed it doesn't "skip" the next element (since it gets shifted down)
                keyword_UW = keyword.upper() + ' ' #Make upper case because of dictionary format. Add space so it is a whole word.
                len_k = len(keyword_UW) #Length of the string
                if keyword_UW in line[0:len_k]:
                    WordList_c.remove(keyword) #Remove the word from checking once it has been found once (SPEED UP!)
                    PhonemeDict[keyword] = line[len_k+1:-1].split(' ')  #removes \n special character from string and separates phonemes into parts in a list
    return PhonemeDict

#%%#########################    Constants   ###################################
digraphs = {		
        "ai":26,
        "ay":27,
        "ch":28,
        "ck":29,
        "ea":30,
        "ee":31,
        "ie":32,
        "kn":33,
        "oa":34,
        "oe":35,
        "oo":36,
        "ph":37,
        "sh":38,
        "ss":39,
        "th":40,
        "ue":41,
        "ui":42,
        "wh":43,
        "wr":44
        }

Phones = {
"AA":1,
"AE":2,
"AH":3,
"AO":4,
"AW":5,
"AY":6,
"B" :7,
"CH":8,
"D" :9,
"DH":10,
"EH":11,
"ER":12,
"EY":13,
"F" :14,
"G" :15,
"HH":16,
"IH":17,
"IY":18,
"JH":19,
"K" :20,
"L" :21,
"M" :22,
"N" :23,
"NG":24,
"OW":25,
"OY":26,
"P" :27,
"R" :28,
"S" :29,
"SH":30,
"T" :31,
"TH":32,
"UH":33,
"UW":34,
"V" :35,
"W" :36,
"Y" :37,
"Z" :38,
"ZH":39,
}
keys = list(Phones.keys())
#%%###########################   Create lists    ##############################
#Construct word list from file
WordList = GetWordList()
print("... WordList loaded: " + str(len(WordList)))

#remove duplicate entries
WordList = list(set(WordList)) 
print("... WordList no duplicates: " + str(len(WordList)))

#Remove words with special characters
for word in reversed(WordList):
	if isspecial(word):
		WordList.remove(word)
print("... WordList filtered: " + str(len(WordList)))

#Construct Phoneme list using Phoneme dictionary with word list
PhonemeDict = MakePhonemeDict(WordList)
WordList2 = list(PhonemeDict.keys()) #differently sorted word list
PhonemeList = list(PhonemeDict.values()) #Phonemes matching the above sorting of word list
print("... PhonemeList loaded: " + str(len(PhonemeList)))

#%%###########################   Calculate    #################################

WordMatrix = Words2MatrixEX(WordList2) if extended else Words2Matrix(WordList2)
print("... WordList converted to matrix")

PhoneMatrix = Phones2Matrix(PhonemeList)
print("... PhoneMatrix constructed")

#Determine the mapping between alphabet to phonemes
Map = np.linalg.lstsq(WordMatrix,PhoneMatrix,rcond=None)[0]
invMap = np.linalg.lstsq(PhoneMatrix,WordMatrix,rcond=None)[0] #Pseudo-inv of the mapping matrix to go from phonome -> letter
print("... Transformation matrix created")

invMap_norm = (1/invMap.max(axis=1) * invMap.T).T #normalizes each column
invMap_norm[invMap_norm<0.0] = np.nan

#%%Create a unique phoneme-grapheme assignment
digkeys = list(digraphs.keys())
Phokeys = list(Phones.keys())
invMap_sorted = np.flip(np.argsort(invMap, axis=None)) #Get sorting indeces of 'flattened' invMap (max to min)
RowCol = np.unravel_index(invMap_sorted, (np.size(invMap,0),np.size(invMap,1))) #Convert to row, col indeces
row_list = []
col_list = []
corr_list = [] #value of the correlation
PhAlU = {}
for ind in range(len(invMap_sorted)): #from max to min...
    row = RowCol[0][ind]
    col = RowCol[1][ind]
    if not row in row_list and not col in col_list: #If neither col or row in the list append it
        row_list.append(row)
        col_list.append(col)
        corr_list.append(invMap[row,col])
        PhAlU[Phokeys[row]] = digkeys[col-26] if col>25 else num2lett(col) #phoneme-grapheme correspondance
    if len(row_list) == 39: #If all the phonemes are added break the loop
        break

#%%###########################   Figures    ###################################
alphs = [chr(97+i) for i in range(26)]
plt.figure()
pc = plt.pcolormesh(invMap,norm=colors.DivergingNorm(vmin=invMap.min(), vcenter=0, vmax=invMap.max()),cmap='RdBu_r',edgecolors='black',lw=0.2,antialiased=True)
plt.scatter(np.array(col_list)+0.5,np.array(row_list)+0.5,s=10,c='magenta')
plt.yticks(np.arange(39)+0.5, list(Phones.keys()), size='x-small')
if extended:
    plt.xticks(np.arange(26+len(digraphs))+0.5, np.append(alphs,list(digraphs.keys())), size='x-small')
else:
    plt.xticks(np.arange(26)+0.5, alphs)
#plt.ylabel('Phoneme')
#plt.xlabel('Alphabet')
plt.tick_params(top=True, right=True, labeltop=True, labelright=True)
plt.gca().set_aspect('equal', adjustable='box')
colorbar(pc,0.3)
plt.show()

#%%
plt.figure()
plt.plot(list(PhAlU.keys()),corr_list,'-')
[plt.text(x,y+0.02,s) for x,y,s in zip(list(PhAlU.keys()),corr_list,list(PhAlU.values()))]
plt.stem(list(PhAlU.keys()),corr_list,linefmt='k--',bottom =-0.1, basefmt=None)
plt.ylim(bottom=0)
plt.xticks(size='x-small')
plt.xlabel('Phoneme')
plt.ylabel('Correlation')

#%%###########################   TXT Output   #################################
ext = '_EX' if extended else ''
#Make a text file of the phone to alphabet conversion
with open(sys.path[0] + '\Phone2AlphabetUnique' + ext + '.txt','w') as outF:
    for ph,al,val in zip(PhAlU.keys(),PhAlU.values(),corr_list):
        outF.write('%2s --> %2s (%g)' % (ph, al, val))
        outF.write("\n")
print('Succesfully generated phoneme to grapheme conversion table text file!')
