#!/usr/bin/env python

# reference: Google custom search API client implementations
# link: https://github.com/google/google-api-python-client/blob/master/samples/customsearch/main.py
# author: jcgregorio@google.com (Joe Gregorio)
from googleapiclient.discovery import build
import json
import argparse



# main
def main(target_precision, query, api, engine):
	# validate search API
	if not api:
		try:
			from secrets import GSEARCH_JSON_API
			api = GSEARCH_JSON_API
		except:
			print "[ERROR] Search API not specified"
			exit(1)
	# validate search engine
	if not engine:
		try:
			from secrets import GSEARCH_ENGINE
			engine = GSEARCH_ENGINE
		except:
			print "[ERROR] Search engine ID not specified"
			exit(1)
	# validate target precision
	if not 0 < target_precision <= 1.0:
		print "[ERROR] target precision {} not in range (0, 1]".format(target_precision)
		exit(1)
	# validate query
	query_terms = query.strip().split(' ')
	if not query_terms:
		print "[ERROR] empty/invalid query string"
		exit(1)



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Relevance Feedback Demo')
	parser.add_argument('target_precision', type=float, help='target precision, (0, 1]')
	parser.add_argument('query', type=str, help='initial query string')
	parser.add_argument('--api', type=str, help='Google search API key')
	parser.add_argument('--engine', type=str, help='Google search engine ID')

	args = vars(parser.parse_args())
	main(**args)
