import os
import urllib
from bs4 import BeautifulSoup
from bs4.element import Comment
"""Web Scraper class

a web scrapping utility to scrape web page contents, specifically only the 
text contents in paragraphs
"""
class WebScraper(object):
    ## the constructor
    #  @param local_dir the local directory containing cached files, type: str
    def __init__(self, local_dir="scrapings"):
        self.dir = local_dir

    ## check if HTML tag is valid
    #  copyright from SO answer: https://stackoverflow.com/a/1983219/7164327
    def __valid_tag(self, elem):
        if elem.parent.name in ['style', 'script', '[document]', 'head', 'title']:
            return False
        elif isinstance(elem, Comment):
            return False
        return True

    ## scraping text contents from given URL
    #  save the texts in a file under self.dir as a cache for future queries
    #  @param url URL to visit, type: str
    #  @return text contents, type: str
    def scrape_text(self, url):
        if not url: return ""

        # mkdir if necessary
        if not os.path.exists(self.dir) and self.dir:
            os.makedirs(self.dir)

        # use hash value of url string to name the cache file
        fname = "{}/{}.txt".format(self.dir, abs(hash(url)))
        
        # try to read from local cached files
        if os.path.exists(fname):
            with open(fname, 'r') as f:
                return f.read()

        # didn't get anything from cache, scrape from webpage
        try:
            page = urllib.urlopen(url).read()
        except Exception as e:
            print "failed to open URL, {}".format(e)
            return ""
        soup = BeautifulSoup(page, 'html.parser')
        texts = filter(self.__valid_tag, soup.findAll(text=True))
        ts = [t for t in texts if t != u'\n']
        contents = u' '.join(ts).encode('ascii', 'ignore')

        # save into local cache file
        with open(fname, 'w') as f:
            f.write(contents)
        return contents
