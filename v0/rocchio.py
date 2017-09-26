from math import log
from invfile import *
from heapq import *

"""Rocchio Relevant Feedback class

Given a list of relevant and irrelevant (based on human feedback) documents 
from a certain set of query terms, Rocchio algorithm generates new query 
terms that are more "relevant"

q = m * q0 + a * (dr1 + dr2 + ... ) / |Dr| - b * (dnr1 + dnr2 + ...) / |Dnr| 
    - q:  new query vector, for word w, q[w] is its relevance measurement 
    - q0: original query vector 
    - Dr: set of relevant documents
    - Dnr: set of irrelevant documents
    - m, a, b: weights of original, relevant and irrelevant vectors

In our case, m is always 0, meaning the terms from original query are discarded.
Each vector element is the word's tf-idf value in the document, e.g. dr1 is a 
vector of tf-idf value of each word in the first document of set Dr. Negative 
weights are treated as 0, so we only consider the words that exist in relevant 
documents.
"""
class Rocchio(object):
    ## the constructor
    #  @param alpha weight of relevant document vectors, type: float
    #  @param beta weight of irrelevant document vectors, type: float
    def __init__(self, alpha=1.0, beta=0.0):
        self.rel = set() # set of relevant documents
        self.rel_size = 0 # number of relevant documents
        self.rel_invf = InvertedFiles() # inverted-files

        self.irrel = set() # set of irrelevant documents
        self.irrel_size = 0
        self.irrel_invf = InvertedFiles()

        self.alpha = alpha # weight of relevant documents
        self.beta = beta # weight of irrelevant documents

        # optionally, maintain a list of stop words, in case 
        # the collection of documents is not enough to derive a 
        # small idf value for words like 'is' and 'the'
        self.stops = self.__gen_stop_words()

    ## generate a set of stop words from local file 'stop.txt', if exists
    #  @return type: set(str)
    def __gen_stop_words(self):
        res = set()
        try:
            with open('stop.txt', 'r') as f:
                for l in f.readlines():
                    res.add(l.rstrip())
        except:
            pass
        return res

    ## update relevant and irrelevant document sets
    #  @param rel/irrel type: list[SearchDocument]
    def __update_docs(self, rel, irrel):
        for doc in rel:
            if doc in self.rel: continue
            self.rel.add(doc)
            self.rel_size += 1
            self.rel_invf.add_document(doc)
        for doc in irrel:
            if doc in self.irrel: continue
            self.irrel.add(doc)
            self.irrel_size += 1
            self.irrel_invf.add_document(doc)

    ## calculate idf of the given word 
    #  document frequency is based on both relevant and irrelevant documents
    #  @param word type: str
    #  @return type: float
    def __idf(self, word):
        # total number of documents (rel and irrel)
        n = self.rel_size + self.irrel_size
        if n == 0: return 0.0
        # number of documents (rel and irrel) the word appears in
        df = self.rel_invf.df(word) + self.irrel_invf.df(word)
        if df == 0: return 0.0
        # idf = log(N/df, 10)
        idf = log(float(n)/df, 10)
        if word in self.stops:
            # for a known stop word, e.g. 'is', 'and', assign
            # an arbitrary small idf
            idf = min(idf, 0.0001)
        return idf

    ## calculate weights of words in relevant documents
    #  @param weights tf-idf vector, type: dict(key:str, value:float)
    #  @param idfs idf values cache, type: dict(key:str, value:float)
    #  @param blacklist words to be ignored, type: list[str]
    def __weight_rel(self, weights, idfs, blacklist):
        for word in self.rel_invf.words():
            if word in blacklist: continue
            # idf
            idfs[word] = idf = self.__idf(word)
            # tf-idf, where tf is obtained from inverted-files
            weights[word] = sum(map(lambda x:log(1+x, 10), \
                self.rel_invf.tfs(word).values())) * idf if idf else 0

    ## update weights of words w.r.t irrelevant documents
    #  for weights(vectors) generated from relevant documents, subtract the 
    #  weights of irrelevance
    #
    #  @param weights tf-idf vector of relevant documents, type: dict(key:str, value:float)
    #  @param idfs idf values cache, type: dict(key:str, value:float)
    def __weight_irrel(self, weights, idfs):
        for word, rel_weight in weights.items():
            # calculate sum of irrelevant weights
            idf = idfs[word]
            irrel_weight = sum(map(lambda x:log(1+x, 10), \
                self.irrel_invf.tfs(word).values())) * idf if idf else 0
            if irrel_weight > 0:
                weights[word] = max(0.0, float(self.alpha) * rel_weight / self.rel_size \
                    - float(self.beta) * irrel_weight / self.irrel_size)

    ## generate k query terms based on relevant and irrelevant documents
    #  after calculating new vector of query terms using Rocchio's algorithm, 
    #  the top k terms with largest weights will be returned
    # 
    #  @param rel relevant documents, type: set(SearchDocument)
    #  @param irrel irrelevant documents, type: set(SearchDocument)
    #  @param blacklist words to be ignored, type: list[str], default []
    #  @param k number of new query terms, type: int
    def generate_query(self, rel, irrel, blacklist=[], k=2):
        # update local data by adding new documents
        self.__update_docs(rel, irrel)

        # the weights of each word, and a cache of idf of each word
        weights, idfs = {}, {}

        # first calculate the weights of each word in relevant documents, 
        # for each word, it is the sum of its tf-idf value in all relevant docs
        self.__weight_rel(weights, idfs, blacklist)

        # if necessary, update the weights w.r.t irrelevant documents
        if self.beta > 0 and self.irrel_size:
            self.__weight_irrel(weights, idfs)

        # find the first k words with maximum weights
        return [i[0] for i in nlargest(k, weights.items(), key=lambda x:x[1])]
