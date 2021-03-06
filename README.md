# Wikipedia-Search-Engine

This project requires making of a search engine over the ~60GB Wikipedia dump. The code consists of indexer.py and search.py. 
Both simple and multi field queries have been implemented. The search returns a ranked list of articles in real time.

## Indexing:
* Parsing: SAX Parser is used to parse the XML corpus.
* Casefolding: Converting Upper Case to Lower Case.
* Tokenisation: It is done using regex.
* Stop Word Removal: Stop words are removed by referring to the stop word (all the stopwords are maintained in stopWords.txt file)
* Stemming: A python library PyStemmer is used for this purpose.
* Creating various index files with word to field postings.
* Multi-way External sorting on the index files to create field based files along with their respective offsets.

## Searching:
* The query given is parsed, processed and given to the respective query handler(simple or field).
* One by one word is searched in vocabulary and the file number is noted.
* The respective field files are opened and the document ids along with the frequencies are noted.
* The documents are ranked on the basis of TF-IDF scores.
* The title of the documents are extracted using title.txt

## Files Produced (during Index creation)
* index*.txt (intermediate files) : It consists of words with their posting list. Eg. d1b2t4c5 d5b3t6l1
* title.txt : It consist of id-title mapping.
* titleOffset.txt : Offset for title.txt
* vocab.txt : It has all the words and the file number in which those words can be found along with the document frequency.
* offset.txt : Offset for vocab.txt
* [b|t|i|r|l|c]*.txt : It consists of words found in various sections of the article along with document id and frequency.
* offset_[b|t|i|r|l|c]*.txt : Offset for various field files.

## How to run:
##### python3 wiki_indexing.py pathtoXMLDumpDirectory stat.txt
- This function takes as input the corpus file and creates the entire index in a field separated manner. 
- It also creates a vocabulary list and a file containg the title-id map. 
- Along with these files, it also creates the offsets for all the files.

##### python3 wiki_search.py queries.txt
* This function takes in queries.txt as argument which contains list of queries. It returns the top K(K being mentioned along with query in queries.txt) results from the Wikipedia corpus.
