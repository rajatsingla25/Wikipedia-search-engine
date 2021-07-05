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

import nltk
nltk.download('stopwords')


stop_words = set(stopwords.words('english')) 

MOD=10000

#creating stopwords dictionary
# with open('stopwords.txt', 'r') as fp :
#     	stop_words = set(fp.read().split('\n'))
# stopwords = defaultdict(int)
# for word in stop_words:
# 	stopwords[word] = 1




#text-cleaning-process
def text_cleaning(text):
	global stopwords
	global countwords
	text = text.encode("ascii", errors="ignore").decode()
	text = re.sub(r'[^A-Za-z0-9]+', r' ', text)
	text = text.split()
	countwords+=len(text)
	text = [word for word in text if not word in stop_words] 
	# text = [word for word in text if stopwords[word] != 1 ]
	stemmer = Stemmer.Stemmer('english')
	return stemmer.stemWords(text)

def processText(text, title):
	st1 = "== references == "
	st2 = "==references=="
	text = text.lower() #Case Folding
	temp = text.split(st1)
	x=1
	if len(temp) == x:
		temp = text.split(st2)

	info = process_info(temp[0])
	title = process_title(title)
	body = process_body(temp[0])

	if len(temp) == x: # If empty then initialize with empty lists
		links = []
		categories = []
	else: 
		categories = process_categories(temp[1])
		links = process_links(temp[1])

	return title, body, info, categories, links

def process_title(text):
	text=text.lower()
	data = text_cleaning(text)
	return data

def process_body(text):
	data = re.sub(r'\{\{.*\}\}', r' ', text)
	data = text_cleaning(data)
	return data

def process_info(text):
	data = text.split('\n')
	flag = -1
	info = []
	st="}}"
	for line in data:
		if re.match(r'\{\{infobox', line):
			info.append(re.sub(r'\{\{infobox(.*)', r'\1', line))
			flag = 0
		elif flag == 0:
			if line == st:
				flag = -1
				continue
			info.append(line)
	data = text_cleaning(' '.join(info))
	return data

def process_categories(text):
	data = text.split('\n')
	categories = []
	for line in data:
		if re.match(r'\[\[category', line):
			categories.append(re.sub(r'\[\[category:(.*)\]\]', r'\1', line))
	data = text_cleaning(' '.join(categories))
	return data

def process_links(text):
	data = text.split('\n')
	links = []
	for line in data:
		if re.match(r'\*[\ ]*\[', line):
			links.append(line)
	data = text_cleaning(' '.join(links))
	return data

def add_words(words,wordSET):
	Dict={}
	for word in words:
		if(Dict.get(word)==None):
			Dict[word]=1
		else:
			Dict[word]+=1
		if(wordSET.get(word)==None):
			wordSET[word]=1
		else:
			wordSET[word]+=1

	return Dict,wordSET

def createIndex(title, body, info, categories, links):
	global p_cnt
	global PostList
	global docID
	global offset
	global f_cnt
	# global poffset
	#adding words and there frequency in respective dictionary
	wordSET={}
	titleDict,wordSET=add_words(title,wordSET)
	bodyDict,wordSET=add_words(body,wordSET)
	infoDict,wordSET=add_words(info,wordSET)
	categoriesDict,wordSET=add_words(categories,wordSET)
	linksDict,wordSET=add_words(links,wordSET)
	
	# print("success",wordSET)
	#creating postings for each respective word
	for word,key in wordSET.items():
		string ='d'+(str(p_cnt))
		if(titleDict.get(word)):
			string += 't' + str(titleDict[word])
		if(bodyDict.get(word)):
			string += 'b' + str(bodyDict[word])
		if(infoDict.get(word)):
			string += 'i' + str(infoDict[word])
		if(categoriesDict.get(word)):
			string += 'c' + str(categoriesDict[word])
		if(linksDict.get(word)):
			string += 'l' + str(linksDict[word])
		PostList[word].append(string)
	p_cnt += 1

	if(p_cnt%MOD==0):
		offset = WriteInFile(PostList, docID, f_cnt , offset)
		PostList = defaultdict(list)
		docID = {}
		f_cnt = f_cnt + 1

	if(p_cnt%500000==0):
		print("page processed",p_cnt)
	

class Handle(xml.sax.ContentHandler):
	def __init__(self):
		self.title = ''
		self.text = ''
		self.data = None
		# self.buffer=None
	def startElement(self, tag, attributes):
		self.data = tag
		if tag == 'title':
			self.data=tag
			# self.buffer=[]
		elif tag == 'text':
			self.data=tag
			# self.buffer=[]

	def endElement(self, tag):
		# if tag=='title':
		#     self.title=' '.join(self.buffer)
		# if tag=='text':
		#     self.text=' '.join(self.buffer)
		if tag == 'page':
			docID[p_cnt] = self.title.strip().encode("ascii", errors="ignore").decode()
			title, body, info, categories, links = processText(self.text, self.title)
			createIndex( title, body, info, categories, links)
			self.data = None
			self.title = ''
			self.text = ''
			self.buffer=None
	def characters(self, content):
		if self.data == 'title':
			self.title = self.title + content
		elif self.data == 'text':
			self.text += content
		# if self.data:
		# 	self.buffer+=content



def WriteInFile(PostList,docID,f_cnt,offset):
	global output_file_name
	

	title_list=[]
	titleoffset=[]
	for key in sorted(docID):
		string = str(key)+' '+docID[key]
		length=len(string)
		offset=1+length+offset
		titleoffset.append(str(offset))
		title_list.append(string)
		

	#writing postings of each word
	postings=[]
	for key in sorted(PostList.keys()):
		string = str(key) + ' ' + ' '.join(PostList[key])
		postings.append(string)
		

	filepath = output_file_name+"InvertedIndex"+str(f_cnt)+".txt"
	# filepath= filepath + str(f_cnt+1) + '.txt'
	with open(filepath, 'w') as fp:
		fp.write('\n'.join(postings))

	#writing title mapped with pagenumber in titleMap.txt 
	filepath=output_file_name+"titleMap.txt"
	with open(filepath,'a') as fp:
		fp.write('\n'.join(title_list))
		fp.write('\n')

	#writing offset for each title of each page
	filepath = output_file_name+'titleOffset.txt'
	with open(filepath, 'a') as fp:
		fp.write('\n'.join(titleoffset))
		fp.write('\n')
	return offset


# def FinalWrite(PostList,poffset):
# 	#writing postings of each word
# 	fpList=[None]*27
# 	foList=[None]*27

# 	for i in range(0,26):
# 		# print(chr(ord('a')+i))
# 		filepath = output_file_name+chr(ord('a')+i)+'.txt'
# 		fpList[i]=open(filepath,'a')
# 		filepath = output_file_name+chr(ord('a')+i)+'_offset.txt'
# 		foList[i]=open(filepath,'a')


# 	postings=[]
# 	postingsoffset=[]
# 	for key in sorted(PostList.keys()):
# 		letter=str(key)[0]
# 		if(letter.isdigit()):
# 			letter='a'
# 		num=ord(letter)-ord('a')
# 		string = str(key) + ' ' + ' '.join(PostList[key])
# 		fpList[num].write(string)
# 		fpList[num].write('\n')
# 		# postings.append(string)
# 		foList[num].write(str(poffset[num]))
# 		foList[num].write('\n')
# 		poffset[num]=1+len(string)+poffset[num]

# 	for i in range(0,26):
# 		fpList[i].close()
# 		foList[i].close()
# 	return poffset

def FinalWrite(PostList,poffset):
	global keycount
	#writing postings of each word
	fpList=[None]*27
	foList=[None]*27

	postings = [[] for i in range(27)]
	postingsoffset=[[] for i in range(27)]
	for key in sorted(PostList.keys()):
		
		letter=str(key)[0]
		if(letter.isdigit()):
		   continue
		keycount+=1
		num=ord(letter)-ord('a')
		string = str(key) + ' ' + ' '.join(PostList[key])
		postings[num].append(string)
		postingsoffset[num].append(str(poffset[num]))
		poffset[num]=1+len(string)+poffset[num]


	for i in range(0,26):
		filepath = output_file_name+chr(ord('a')+i)+'.txt'
		fpList[i]=open(filepath,'a')
		filepath = output_file_name+chr(ord('a')+i)+'_offset.txt'
		foList[i]=open(filepath,'a')
		if(len(postings[i])>0):
			fpList[i].write('\n'.join(postings[i]))
			fpList[i].write('\n')
			foList[i].write('\n'.join(postingsoffset[i]))
			foList[i].write('\n')
		fpList[i].close()
		foList[i].close()
	return poffset


def mergefiles(filecount):
	line=[None]*(filecount+1)
	filePointers=[None]*(filecount+1)
	i=0
	isend=[False]*(filecount)
	wordmap=[]
	poffset=[0]*27
	heap=[]
	for i in range(0,filecount):
		filename=output_file_name+"InvertedIndex"+str(i)+".txt"
		filePointers[i]=open(filename,'r')
		line[i]=filePointers[i].readline().strip().split()
		
		
		
		if line[i]!=None and len(line[i])>1:
			isend[i]=True
			if line[i][0] not in heap:
				heapq.heappush(heap,line[i][0])
		i+=1

	i=0
	posting=defaultdict(list)
	count=0
	while (any(isend)== True):
		word=heapq.heappop(heap)
		# print(word)
		# isend[i]=False
		for i in range(0,filecount):
			if line[i]!=None and len(line[i])>0 and line[i][0]==word:
				posting[word].extend(line[i][1:])
				line[i]=filePointers[i].readline().strip().split()
				if(len(line[i])==0):
					isend[i]=False
					filePointers[i].close()
					filename=output_file_name+"InvertedIndex"+str(i)+".txt"
					os.remove(filename)
				else:
					if line[i][0] not in heap:
						heapq.heappush(heap,line[i][0])
		count+=1
		if(count%10000==0):
			poffset = FinalWrite(posting,poffset)
			posting = defaultdict(list)
			if(count%1000000==0):
				print("processed words ",count)

	if(len(PostList)>0):
		# print(len(PostList))
		poffset = FinalWrite(posting,poffset)



if __name__ == '__main__':

	start=time.time()
	docID = {} ## {Doc id : Title}
	p_cnt = 0 ### Page Count
	f_cnt = 0 ### File Count
	offset = 0 ## Offset
	PostList = defaultdict(list)
	countwords=0
	keycount=0
	# input_file_name=sys.argv[1]
	input_file_name="input_files/"
	# "1.xml-p1p30303"
	# output_file_name=sys.argv[2]
	output_file_name="inverted_index/"
	# stat_file_path=sys.argv[3]
	stat_file_path="invertedindex_stat.txt"
	##### Begin Parsing
	parser = xml.sax.make_parser()
	parser.setFeature(xml.sax.handler.feature_namespaces, 0)
	handler = Handle()
	parser.setContentHandler(handler)
	for i in range(1,35):
		ippath=input_file_name+str(i)+".xml"
		parser.parse(ippath)

	print("Number of Pages Processed",p_cnt)
	filepath=output_file_name+'totalPages.txt'
	with open(filepath, 'w') as f:
		f.write(str(p_cnt))

	offset = WriteInFile(PostList, docID, f_cnt , offset)
	f_cnt+=1
	end=time.time()
	print("Time taken : ",end-start)
	print("word count : ", countwords)
	mergefiles(f_cnt)
	print("Tokens count :",keycount)

	with open(stat_file_path, 'w') as f:
		f.write(str(countwords))
		f.write('\n')
		f.write(str(keycount))
	
	
