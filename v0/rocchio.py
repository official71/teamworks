from math import log

class Rocchio(object):
    """Rocchio Relevant Feedback"""
    def __init__(self, alpha=1.0, beta=0.0):
        self.rel = None # set of relevant documents
        self.irrel = None # set of irrelevant documents
        self.alpha = alpha # weight of relevant documents
        self.beta = beta # weight of irrelevant documents

        # the idf of each word, defined by log10(N/df),
        # where N is the total number of documents,
        # and df is the word's document frequency, i.e. number of documents 
        # the word appears in
        self.idf = {}

        # for each word, calculate its weight w.r.t its tf-idf value in 
        # both rel (r) and irrel (i), the weight is:
        # w = alpha * r / size(rel) - beta * i / size(irrel)
        self.weights = {}

        # optionally, maintain a list of stop words
        self.stops = self.__gen_stop_words()
        
    def __gen_stop_words(self):
        res = set()
        try:
            with open('stop.txt', 'r') as f:
                for l in f.readlines():
                    res.add(l.rstrip())
        except:
            pass
        return res

    def __update_data(self, rel, irrel):
        self.rel = rel
        self.irrel = irrel
        self.idf = {}
        self.weights = {}

    # assign idf for each word
    def build_idf(self):

        def idf_for_set(st):
            for d in st:
                for w in d.tf:
                    if not w in self.idf:
                        self.idf[w] = 1
                    else:
                        self.idf[w] += 1
        # count document frequency for each word in both rel and irrel sets
        idf_for_set(self.rel)
        idf_for_set(self.irrel)
        # log(N/df)
        N = len(self.rel) + len(self.irrel)
        if N > 0:
            for k, v in self.idf.items():
                self.idf[k] = log(float(N)/v, 10)
                if k in self.stops:
                    # for stop words e.g. 'is', assign an arbitary small idf
                    self.idf[k] = min(self.idf[k], 0.001)
        return N > 0

    # calculate the weights of each word in relevant documents
    # every word in relevant documents are candidates for the new query string
    def weight_rel(self, orig):
        for doc in self.rel:
            for word, tf in doc.tf.items():
                # ignore words in original query
                if word in orig: continue
                # tf-idf value
                tval = log(1+tf, 10) * self.idf.get(word, 0.0)
                if not word in self.weights:
                    self.weights[word] = tval
                else:
                    self.weights[word] += tval

    # calculate the weights of each word in irrelevant documents
    # only care about the words already in relevant documents
    def weight_irrel(self):
        for word, rv in self.weights.items():
            # sum of irrelevant weights
            s = 0
            for doc in self.irrel:
                if word in doc.tf:
                    s += log(1+doc.tf[word], 10) * self.idf.get(word, 0.0)
            if s > 0:
                # irrelevant weight exists, update weight
                self.weights[word] = max(0.0, float(self.alpha) * rv / len(self.rel) - \
                    float(self.beta) * s / len(self.irrel))

    # update query
    def update_query(self, rel, irrel, orig=[], incr=2):
        self.__update_data(rel, irrel)

        # calculate idf
        if not self.build_idf():
            return []

        # first calculate the weights of each word in relevant documents
        self.weight_rel(orig)

        # if necessary, update the weights w.r.t irrelevant documents
        if self.beta > 0:
            self.weight_irrel()

        # find the first $incr words with maximum weights
        res = sorted(self.weights.items(), key=lambda x:-x[1])
        return [i[0] for i in res[:min(incr, len(res))]]

