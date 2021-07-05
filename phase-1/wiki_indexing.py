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

stop_words = set(stopwords.words('english')) 

MOD=20000

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
        temp = text.split('st2')

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

	if(p_cnt%1000==0):
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
    global keycount

    title_list=[]
    titleoffset=[]
    for key in sorted(docID):
    	string = str(key)+' '+docID[key]
    	length=len(string)
    	offset=1+length+offset
    	titleoffset.append(str(offset))
    	title_list.append(string)
    	keycount+=1

    #writing postings of each word
    postings=[]
    postingsoffset=[]
    poffset=0
    for key in sorted(PostList.keys()):
    	string = str(key) + ' ' + ' '.join(PostList[key])
    	postings.append(string)
    	postingsoffset.append(str(poffset))
    	poffset=1+len(string)+poffset

    filepath = output_file_name+"InvertedIndex.txt"
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
    #writing offset for each word
    filepath = output_file_name+'postingOffset.txt'
    with open(filepath, 'a') as fp:
    	fp.write('\n'.join(postingsoffset))
    	fp.write('\n')
    return offset

if __name__ == '__main__':

    start=time.time()
    docID = {} ## {Doc id : Title}
    p_cnt = 0 ### Page Count
    f_cnt = 0 ### File Count
    offset = 0 ## Offset
    PostList = defaultdict(list)
    countwords=0
    keycount=0
    input_file_name=sys.argv[1]
    # "sample.xml"
    #"1.xml-p1p30303"
    output_file_name=sys.argv[2]
    stat_file_path=sys.argv[3]
    ##### Begin Parsing
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    handler = Handle()
    parser.setContentHandler(handler)
    parser.parse(input_file_name)

    print("Number of Pages Processed",p_cnt)
    filepath=output_file_name+'totalPages.txt'
    with open(filepath, 'w') as f:
        f.write(str(p_cnt))

    offset = WriteInFile(PostList, docID, f_cnt , offset)
    end=time.time()
    print("Time taken : ",end-start)
    print(countwords)
    print(keycount)
    with open(stat_file_path, 'w') as f:
        f.write(str(countwords))
        f.write('\n')
        f.write(str(keycount))
