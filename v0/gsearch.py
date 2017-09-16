# reference: Google custom search API client implementations
# link: https://github.com/google/google-api-python-client/blob/master/samples/customsearch/main.py
# author: jcgregorio@google.com (Joe Gregorio)
from googleapiclient.discovery import build
import json
import re

class SearchDocument(object):
	def __init__(self, fields, rank=None):
		self.rank = rank
		self.title = fields['title']
		self.displink = fields['displayLink']
		self.url = fields['formattedUrl']
		self.snippet = fields['snippet']
		self.key = self.url + '|' + self.title
		# statistics of terms in document
		self.words = self.parse(self.title) + self.parse(self.snippet)
		self.size = len(self.words)
		self.tf = self.get_tf()

	# normalized term frequency of each word
	def get_tf(self):
		res = {}
		for word in self.words:
			if not word in res:
				res[word] = 1
			else:
				res[word] += 1
		# normalize
		for word, v in res.items():
			res[word] = float(v) / self.size
		return res

	# convert string to list of lowercase words w/o punctuations
	def parse(self, s):
		res = []
		for w in s.split():
			r = re.sub(r'[\W_]', '', w.lower())
			if r:
				res.append(r)
		return res

# execute search and get the json formatted result
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

#
def gsearch(query, api, engine):
	raw = gsearch_exec(query, api, engine)
	return [SearchDocument(i) for i in raw['items']]
