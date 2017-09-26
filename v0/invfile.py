from collections import defaultdict
from math import log
from gsearch import SearchDocument

"""Inverted-files class

Inverted-files is a common data structure used for information retrieval, 
it contains the bag of words in a collection of documents, as well as 
information associated to the words. In this implementation, a hash table 
is used, where key is the word, and value is also a hash table which 
contains the (document, term frequency) pairs of the word. The term 
frequency is in absolute number, NOT normalized.
"""
class InvertedFiles(object):
    ## the constructor
    #  @param docs collection of documents, type: list[SearchDocument]
    def __init__(self, docs=[]):
        self.__docs = []
        self.__data = defaultdict(dict) # the inverted-file data
        # add docs
        for doc in docs:
            self.add_document(doc)

    ## add one document to the collection
    #  @param doc type: SearchDocument
    def add_document(self, doc):
        if not doc:
            return
        if not isinstance(doc, SearchDocument):
            raise ValueError("invalid type: {}".format(type(doc)))

        self.__docs.append(doc)
        # SearchDocument.tf contains {word: term frequency} mapping of the doc
        for word, freq in doc.tf.items():
            self.__data[word][doc] = freq

    ## size of bag of words in the collection
    #  @return type: int
    def nr_words(self):
        return len(self.__data)

    ## number of documents in the collection
    #  @return type: int
    def nr_docs(self):
        return len(self.__docs)

    ## list of words in the collection
    #  @return type: list[str]
    def words(self):
        return self.__data.keys()

    ## document frequency of the given word
    #  df is the absolute number of documents that the word exists in
    #  @param word type: str
    #  @return type: int
    def df(self, word):
        return len(self.__data[word])

    ## inverse document frequency of the given word
    #  idf is log(N/df), where N is the total number of documents, 
    #  if df or N is 0, return 0.0; log is base 10
    #  @param word type: str
    #  @return type: float
    def idf(self, word):
        # total number of documents
        n = len(self.__docs)
        if n == 0: return 0.0
        # number of documents the word appears in
        df = self.df(word)
        if df == 0: return 0.0
        # idf = log(N/df, 10)
        return log(float(n)/df, 10)

    ## term frequencies of the given word in documents
    #  tf is the absolute number of appearances of the word in a document, 
    #  for data protection a copy of the data is returned
    #  @param word type: str
    #  @return type: dict(key:SearchDocument, value:int)
    def tfs(self, word):
        return dict(self.__data[word])
