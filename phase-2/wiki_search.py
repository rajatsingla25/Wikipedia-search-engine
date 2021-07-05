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
import math

import nltk
nltk.download('stopwords')

stop_words = set(stopwords.words('english')) 

#creating stopwords dictionary
# with open('stopwords.txt', 'r') as fp :
#         stop_words = set(fp.read().split('\n'))
# stopwords = defaultdict(int)
# for word in stop_words:
#     stopwords[word] = 1


#text-cleaning-process
def text_cleaning(text):
	global stopwords
	text = text.encode("ascii", errors="ignore").decode()
	text = re.sub(r'[^A-Za-z0-9]+', r' ', text)
	text = text.split()
	text = [word for word in text if not word in stop_words] 
	# text = [word for word in text if stopwords[word] != 1 ]
	stemmer = Stemmer.Stemmer('english')
	return stemmer.stemWords(text)

def findPostings(word):
	global Index_file_path
	filename=Index_file_path + 'totalPages.txt'
	f = open(filename, 'r')
	nfiles = int(f.read().strip())
	f.close()
	letter=word[0]
	if(letter.isdigit()):
		letter='a'
	filename=Index_file_path +letter+'.txt'
	indexFilePointer = open(filename, 'r')
	low=0
	# high=nfiles
	offset=[]
	filepath = Index_file_path +letter+'_offset.txt'
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
				return wordPtr[1:]
			elif word <= wordPtr[0]:
				high = mid
			else:
				low = mid + 1
		else :
			break
	return []


def find_ranking_s(postlist):
	fact={}
	fact['t']=float(0.9)
	fact['b']=float(0.5)
	fact['i']=float(0.7)
	fact['c']=float(0.6)
	fact['l']=float(0.6)
	weightedDOCS=defaultdict(float)
	# docfreq={}
	filepath = Index_file_path + 'totalPages.txt'
	fp = open(filepath, 'r')
	totalDocs = float(fp.read().strip())
	fp.close()
	for key in postlist.keys():
		doclist=postlist[key]
		N=len(doclist)
		if N>0:
			IDF=math.log(totalDocs/N)
		else:
			return weightedDOCS
		# print(postlist[key])
		for rex in doclist:
			# print(rex)
			docID = re.sub(r'.*d([0-9]*).*', r'\1', rex)
			# print(docID)
			temp = re.sub(r'.*c([0-9]*).*', r'\1', rex)
			if len(temp)>0 and rex!= temp:
				weightedDOCS[docID]=weightedDOCS[docID]+(1+math.log(float(temp)))*IDF*fact['c']

			temp = re.sub(r'.*i([0-9]*).*', r'\1', rex)
			if len(temp)>0 and rex!= temp:
				weightedDOCS[docID]=weightedDOCS[docID]+(1+math.log(float(temp)))*IDF*fact['i']

			temp = re.sub(r'.*l([0-9]*).*', r'\1', rex)
			if len(temp)>0 and rex!= temp:
				weightedDOCS[docID]=weightedDOCS[docID]+(1+math.log(float(temp)))*IDF*fact['l']

			temp = re.sub(r'.*b([0-9]*).*', r'\1', rex)
			if len(temp)>0 and rex!= temp:
				weightedDOCS[docID]=weightedDOCS[docID]+(1+math.log(float(temp)))*IDF*fact['b']

			temp = re.sub(r'.*t([0-9]*).*', r'\1', rex)
			if len(temp)>0 and rex!= temp:
				weightedDOCS[docID]=weightedDOCS[docID]+(1+math.log(float(temp)))*IDF*fact['t']

		# 	print(weightedDOCS[docID])
		# print("success")

	return weightedDOCS
	
def find_ranking_f(postlist,fieldMap,totalDocs):
	# print("field")
	fact={}
	fact['t']=float(900)
	fact['b']=float(500)
	fact['i']=float(700)
	fact['c']=float(600)
	fact['l']=float(600)
	weightedDOCS=defaultdict(float)
	# docfreq={}

	for key in postlist.keys():
		# print(key)
		doclist=postlist[key]
		N=len(doclist)
		if N>0:
			IDF=float(math.log(totalDocs/N))
		else:
			return weightedDOCS
		f=fieldMap[key]
		
		for rex in doclist:
			# print(rex)
			docID = re.sub(r'.*d([0-9]*).*', r'\1', rex)
			# print(docID)
			
			if(f=="c"):
				temp = re.sub(r'.*c([0-9]*).*', r'\1', rex)
			elif(f=="b"):
				temp = re.sub(r'.*b([0-9]*).*', r'\1', rex)
			elif(f=="t"):
				temp = re.sub(r'.*t([0-9]*).*', r'\1', rex)
			elif(f=="l"):
				temp = re.sub(r'.*l([0-9]*).*', r'\1', rex)
			elif(f=="i"):
				temp = re.sub(r'.*i([0-9]*).*', r'\1', rex)
			else:
				continue
			
			if len(temp)>0 and rex!= temp:
				weightedDOCS[docID]=weightedDOCS[docID]+(1+math.log(float(temp)))*IDF*fact[f]
		

		# 	print(weightedDOCS[docID])
		# print("success")

	return weightedDOCS



def Title_Map(docID):
	global Index_file_path
	filename=Index_file_path + 'totalPages.txt'
	f = open(filename, 'r')
	nfiles = int(f.read().strip())
	f.close()
	filename=Index_file_path + 'titleMap.txt'
	indexFilePointer = open(filename, 'r')
	low=0
	high=nfiles
	offset=[]
	filepath = Index_file_path + 'titleOffset.txt'
	with open(filepath, 'r') as f:
		for line in f:
			if(len(line)>1):
				offset.append(int(line.strip()))
	# high=len(offset)
	while True:
		if low<high :
			mid = int((low + high) / 2)
			indexFilePointer.seek(offset[mid])
			wordPtr = indexFilePointer.readline().strip().split()

			if wordPtr[0] == docID:
				return wordPtr[1:]
			elif docID <= wordPtr[0]:
				high = mid
			else:
				low = mid + 1
		else :
			break
	return []




def begin_search(query_file):
	print('-------- Wikipedia Search Engine -------\n\n')

	TitleDict=defaultdict(str)
	filename=Index_file_path + 'titleMap.txt'
	f=open(filename,'r')
	for line in f:
		line=f.readline().strip().split()
		if(len(line)>0):
			ID=line[0].strip()
			line=' '.join(line[1:])
			# print(line)
			TitleDict[ID]=line.strip()
		# print(line)
	f.close()
	fp1=open('queries_op.txt','a')
	fp=open(query_file,'r')
	filepath = Index_file_path + 'totalPages.txt'
	fp2 = open(filepath, 'r')
	totalDocs = float(fp2.read().strip())
	fp2.close()
	for line in fp:
		line=line.strip().split(',')
		# print(line)
		query=line[1].strip()
		k=int(line[0])
		print("Given Query : ",query)

		query = query.lower()
		start = time.time()
		flag=None
		fieldMap={}
		if re.match(r'[t|b|i|c|l]:', query):
			listOfFields = re.findall(r'([b|c|i|l|t|r]):', query)
			# print(listOfFields)
			flag='f'
			words = re.findall(r'[t|b|c|i|l|r]:([^:]*)(?!\S)', query)
			# print(words)
			numberofwords=len(words)
			tokens=[]
			fields=[]
			i=0
			while(i<numberofwords):
				tempTokens=text_cleaning(words[i])
				# print(tempTokens)
				for w in tempTokens:
					tokens.append(w)
					fieldMap[w]=listOfFields[i]
				i+=1
			
		else:
			tokens = text_cleaning(query)

		postlist=defaultdict(list)
		for word in tokens:
			postlist[word]=findPostings(word)
			# print(postlist[word])
			
			

		if(flag=='f'):
			res=find_ranking_f(postlist,fieldMap,totalDocs)
		else:
			res=find_ranking_s(postlist)
		# print(res)
		if len(res) > 0:
			res= sorted(res, key=res.get, reverse=True)
			res= res[:k]
			# print(res)
		# print("Results\n")
		end = time.time()
		# print(TitleDict[str(1)])
		for key in res:
			# print(key)
			# title = Title_Map(key)
			# print(title)
			title = TitleDict[key]
			# print(title)
			if(len(title)>0):
				# print(' '.join(title))
				fp1.write(key)
				fp1.write(', ')
				fp1.write(title)
				fp1.write('\n')
		
		ms=(end-start)
		print('Time taken: ',str(ms))
		fp1.write(str(ms))
		fp1.write(' sec\n\n\n')

	fp.close()
	fp1.close()

if __name__ == '__main__':
	# offset,titleOffset = [],[]
	Index_file_path="inverted_index/"
	query_file=sys.argv[1]
	begin_search(query_file)
