#!/usr/bin/env python

import argparse
from gsearch import *
from rocchio import *


def validate(args):
	# validate search API
	api = args.api
	if not api:
		try:
			from secrets import GSEARCH_JSON_API
			api = GSEARCH_JSON_API
		except:
			print "[ERROR] Search API not specified"
			exit(1)
	# validate search engine
	engine = args.engine
	if not engine:
		try:
			from secrets import GSEARCH_ENGINE
			engine = GSEARCH_ENGINE
		except:
			print "[ERROR] Search engine ID not specified"
			exit(1)
	# validate target precision
	target_precision = args.target_precision
	if not 0 < target_precision <= 1.0:
		print "[ERROR] target precision {} not in range (0, 1]".format(target_precision)
		exit(1)
	# validate query
	query_terms = args.query.strip().split(' ')
	if not query_terms:
		print "[ERROR] empty/invalid query string"
		exit(1)

	# all set, return validated arguments
	return target_precision, query_terms, api, engine

'''
collect user feedbacks on the documents returned by search engine,
the feedback is binary Y/N indicating whether the document is relevant.
'''
def feedback(docs):
	# to save human effort, we save the previous feedbacks in two files: 
	# "tmp/rel.txt" and "tmp/irrel.txt", where each row is the key of a doc
	def f2set(f):
		res = set()
		for line in f.readlines():
			r = line.rstrip()
			if r: res.add(r)
		return res

	try:
		rf = open('tmp/rel.txt', 'r+')
		irf = open('tmp/irrel.txt', 'r+')
		rels, irrels = f2set(rf), f2set(irf)
		print "ok"
	except:
		rf = irf = None
		rels = irrels = []

	# for each document, require user feedback if not already in rels/irrels
	rel, irrel = set(), set()
	for doc in docs:
		print "\n" + "-" * 36
		print doc.url
		print doc.title
		print doc.snippet

		if doc.key in rels:
			print "\nalready marked relevant, continue..."
			rel.add(doc)
		elif doc.key in irrels:
			print "\nalready marked irrelevant, continue..."
			irrel.add(doc)
		else:
			i = raw_input("\nIs this relevant (Y/N)? ")
			if i.strip().lower() in ['y', 'yes']:
				print "mark relevant..."
				rel.add(doc)
				if rf: rf.write(doc.key + '\n')
			else:
				print "mark irrelevant..."
				irrel.add(doc)
				if irf: irf.write(doc.key + '\n')
	print "... Done\n"

	l1, l2 = len(rel), len(irrel)
	p = float(l1) / (l1 + l2) if l1 > 0 else 0
	return rel, irrel, p

# main
def main(args):
	target_precision, query_terms, api, engine = validate(args)
	iteration, precision = 0, 0.0
	while iteration == 0 or precision < target_precision:
		# apply search on the current query terms
		docs = gsearch(" ".join(query_terms), api, engine)
		
		# collect user feedback
		rel, irrel, precision = feedback(docs)
		print "[iteration: %2d] %d relevant, %d irrelevant, %.1f precision" % \
			(iteration, len(rel), len(irrel), precision)

		if precision >= target_precision:
			# target achieved
			print "target precision %.1f has been achieved" % target_precision
			break
		elif precision == 0:
			# no need to move on
			print "no need to continue under zero precision"
			break

		# update query string
		break

		iteration += 1
		if iteration >= 10:
			# maximum iteration
			print "maximum iteration exceeded"
			break

	print "Exit...\n"

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Relevance Feedback Demo')
	parser.add_argument('target_precision', type=float, help='target precision, (0, 1]')
	parser.add_argument('query', type=str, help='initial query string')
	parser.add_argument('--api', type=str, help='Google search API key')
	parser.add_argument('--engine', type=str, help='Google search engine ID')

	# args = vars()
	main(parser.parse_args())
