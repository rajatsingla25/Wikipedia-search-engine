#import packages
from collections import defaultdict
import time
import xml.sax
from unidecode import unidecode
import sys
import re
import Stemmer
import heapq
import operator
import os
import pdb
import threading
from tqdm import tqdm
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 

#creating stopwords dictionary
with open('stopwords.txt', 'r') as fp :
        stop_words = set(fp.read().split('\n'))
stopwords = defaultdict(int)
for word in stop_words:
    stopwords[word] = 1


#text-cleaning-process
def text_cleaning(text):
    global stopwords
    text = text.encode("ascii", errors="ignore").decode()
    text = re.sub(r'[^A-Za-z0-9]+', r' ', text)
    text = text.split()
    text = [word for word in text if stopwords[word] != 1 ]
    stemmer = Stemmer.Stemmer('english')
    return stemmer.stemWords(text)

def findPostings(word):
    global Index_file_path
    filename=Index_file_path + 'totalPages.txt'
    f = open(filename, 'r')
    nfiles = int(f.read().strip())
    f.close()
    filename=Index_file_path + 'InvertedIndex.txt'
    indexFilePointer = open(filename, 'r')
    low=0
    # high=nfiles
    offset=[]
    filepath = Index_file_path + 'postingOffset.txt'
    with open(filepath, 'r') as f:
        for line in f:
            offset.append(int(line.strip()))
    high=len(offset)
    while True:
        if low<high :
            mid = int((low + high) / 2)
            indexFilePointer.seek(offset[mid])
            wordPtr = indexFilePointer.readline().strip().split()
            # print(wordPtr)
            # print(mid)

            if wordPtr[0] == word :
                return mid,wordPtr[1:]
            elif word <= wordPtr[0]:
                high = mid
            else:
                low = mid + 1
        else :
            break
    return -1,[]

def begin_search(query):
    print('-------- Wikipedia Search Engine -------\n')

    query = query.lower()
    start = time.time()
    if re.match(r'[t|b|i|c|l]:', query):
        listOfFields = re.findall(r'([b|c|i|l|t]):', query)
        # print(listOfFields)
        words = re.findall(r'[t|b|c|i|l]:([^:]*)(?!\S)', query)
        # print(words)
        numberofwords=len(words)
        tokens=[]
        fields=[]
        i=0
        while(i<numberofwords):
        	tempTokens=text_cleaning(words[i])
        	print(tempTokens)
        	for w in tempTokens:
        		fields.append(listOfFields[i])
        		tokens.append(w)
        	i+=1
        # print("here",tokens)
        # print("here",fields)
        
    else:
        tokens = text_cleaning(query)
        # print("here",tokens)

    postlist=defaultdict(list)
    for word in tokens:
    	postlist[word]=findPostings(word)
    	if len(postlist[word])>0:
    		print(word)
    		print(postlist[word])
    end = time.time()
    print('Time taken: ', end-start)

if __name__ == '__main__':
    # offset,titleOffset = [],[]
    Index_file_path=sys.argv[1]
    query=' '.join(sys.argv[2:])
    begin_search(query)
