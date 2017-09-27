# reference: Google custom search API client implementations
# link: https://github.com/google/google-api-python-client/blob/master/samples/customsearch/main.py
# author: jcgregorio@google.com (Joe Gregorio)
from googleapiclient.discovery import build
import json
import re
from collections import Counter
from nltk.stem.snowball import SnowballStemmer
from scraper import WebScraper

"""Search Document class

a document returned by Google search engine, extracted from the 'item' part 
of the JSON data returned by Google search API, including information such as 
the title, URL link, and a snippet of document. Also include some statistical 
information such as term frequency of each word.
"""
class SearchDocument(object):
    ## global stemming engine
    try:
        stemmer = SnowballStemmer("english")
    except Exception as e:
        print "SearchDocument class failed to initialize stemming engine: {}".format(e)
        stemmer = None
    ## global cache of word stemming to reduce calling snowball stemming API
    cache_stemming = {}
    scraper = WebScraper()

    ## the constructor
    #  @param fields "items" of Google search results, type: dict
    #  @param stemming (False) True to enable stemming, e.g. stem("apples") = "apple"
    #  @param htmltext (False) True to use the html text instead of snippet
    #  @param normalize (False) True to have term frequency instead of raw counts
    def __init__(self, fields, stemming=False, htmltext=False, normalize=False):
        self.title = fields['title']
        self.displink = fields['displayLink']
        self.url = fields['link'] # 'link' is the complete URL, not 'formattedUrl'
        self.snippet = fields['snippet']
        self.key = self.url
        self.text = self.scraper.scrape_text(self.url) if htmltext else ""
        self.stemming = stemming

        # all words in document (with duplicates)
        if htmltext:
            self.words = self.__parse(self.text)
        else:
            self.words = self.__parse(self.title) + self.__parse(self.snippet)
        # document length
        self.size = len(self.words)
        # term count/frequency
        self.tf = self.__tf(normalize)

    ## calculate terms occurence/frequency
    def __tf(self, normalize):
        res = Counter(self.words)
        if normalize:
            for word, count in res.items():
                res[word] = float(count)/self.size
        return res

    ## apply word stemming if necessary
    def __stem(self, word):
        if not self.stemming or not self.stemmer:
            # stemming is disabled
            return word
        elif word in self.cache_stemming:
            # found in cache
            return self.cache_stemming[word]
        else:
            # stem, and save in cache
            stemmed = self.cache_stemming[word] = self.stemmer.stem(word)
            return stemmed

    ## convert string to list of lowercase words w/o punctuations
    def __parse(self, s):
        res = []
        for w in s.split():
            r = re.sub(r'[\W_]', '', self.__stem(w.lower()))
            if r:
                res.append(r)
        return res

## execute search and get the JSON formatted result
#  @param api the Google search API key, type: str
#  @param engine the Google search engine ID, type: str
#  @return type: dict
def gsearch_exec(query, api, engine):
    # first try to fetch the search result from saved results on disk,
    # keep in mind that Google charges you fees if you call the API too many times a day!
    fname = 'tmp/q_' + '-'.join(query.split()) + '.txt'
    try:
        with open(fname, 'r') as f:
            res = json.load(f)
        return res
    except:
        pass

    # Build a service object for interacting with the API. Visit
    # the Google APIs Console <http://code.google.com/apis/console>
    # to get an API key for your own application.
    service = build("customsearch", "v1", developerKey=api)
    res = service.cse().list(q=query, cx=engine).execute()
    
    # save the res into tmp file
    with open(fname, 'w') as f:
        json.dump(res, f)
    return res

## apply Google search
#  @param query query terms, type: str
#  @param api the Google search API key, type: str
#  @param engine the Google search engine ID, type: str
#  @return list of returned documents, type: list[SearchDocument]
def gsearch(query, api, engine):
    raw = gsearch_exec(query, api, engine)

    ##
    # when cosntructing the documents, several decisions should be made:
    #
    # - do word stemming? 
    #   yes, if 'car' is already in the query terms, we don't need to add 'cars' anymore
    #
    # - term frequency or raw counts?
    #   frequency, although in our case the documents all have similar size because 
    #   they are derived from API results
    #
    # - document is from the snippet or raw text of the source webpage?
    #   snippet, experiments have shown poor results if we use raw text of webpages 
    #   by "scraping" on our own. The scraped data is uneven in both size and quality 
    #   among documents, and contains too much noise without any processing; on the 
    #   other hand, the snippet returned by Google API gives the best summary of the 
    #   webpage's contents (although mostly the contents around the keywords we searched 
    #   for), besides it's much smaller in size and easier to process 
    #   
    return [SearchDocument(i, stemming=True, normalize=True) for i in raw['items']]
