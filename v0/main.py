#!/usr/bin/env python

import argparse
from gsearch import *
from rocchio import *
from termcolor import colored
from nltk.stem.snowball import SnowballStemmer

nocol = False # no colors
stemmer = SnowballStemmer("english")

## color the string based on its type
#  @param s string, type: str
#  @param t type of string, type: str
def color(s, t='default'):
    if nocol or not s:
        return s
    # colorful
    if t == 'rel':
        return colored(s, 'green')
    elif t == 'irrel':
        return colored(s, 'red')
    elif t == 'key':
        return colored(s, 'green', attrs=['underline'])
    elif t == 'delim':
        return colored(s, 'yellow', attrs=['bold'])
    elif t == 'strong':
        return colored(s, 'magenta', attrs=['bold'])
    elif t == 'error':
        return colored(s, 'red')
    else:
        return colored(s, 'white')

## highlight keywords in string
#  @param string type: str
#  @param keywords type: list[str]
def highlight_keywords(string, keywords):
    if nocol:
        return string
    string = string.encode('ascii', 'ignore')
    keys = [stemmer.stem(w) for w in keywords]
    res = []
    for i, w in enumerate(string.split()):
        if stemmer.stem(filter(str.isalnum, w.lower())) in keys:
            res.append(color(w, 'key'))
        else:
            res.append(color(w))
    return " ".join(res)

## validate input arguments
def validate(args):
    # validate search API
    api = args.api
    if not api:
        try:
            from secrets import GSEARCH_JSON_API
            api = GSEARCH_JSON_API
        except:
            print color("[ERROR] Search API not specified", "error")
            exit(1)
    # validate search engine
    engine = args.engine
    if not engine:
        try:
            from secrets import GSEARCH_ENGINE
            engine = GSEARCH_ENGINE
        except:
            print color("[ERROR] Search engine ID not specified", "error")
            exit(1)
    # validate target precision
    target_precision = args.target_precision
    if not 0 < target_precision <= 1.0:
        print color("[ERROR] target precision {} not in range (0, 1]".format(
            target_precision), "error")
        exit(1)
    # validate query
    query_terms = [unicode(i) for i in args.query.strip().split(' ')]
    if not query_terms:
        print color("[ERROR] empty/invalid query string", "error")
        exit(1)

    # all set, return validated arguments
    return target_precision, query_terms, api, engine


## collect user feedbacks on the documents returned by search engine,
#  the feedback is binary Y/N indicating whether the document is relevant.
#  @param docs documents returned by search engine, type: list[SearchDocument]
def feedback(docs, keywords):
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
    except:
        rf = irf = None
        rels = irrels = []

    # for each document, require user feedback if not already in rels/irrels
    rel, irrel = set(), set()
    c = 0
    for doc in docs:
        c += 1
        print color("-" * 30 + format(c, '^3d') + "-" * 30, "delim")
        print color("    URL: " + doc.url)
        print color("  Title: ") + highlight_keywords(doc.title, keywords)
        print color("Snippet: ") + highlight_keywords(doc.snippet, keywords)

        if doc.key in rels:
            print "\n" + color("already marked relevant, continue...", "rel")
            rel.add(doc)
        elif doc.key in irrels:
            print "\n" + color("already marked irrelevant, continue...", "irrel")
            irrel.add(doc)
        else:
            i = raw_input("\n" + color("Is this relevant (" + \
                color("Y", "rel") + color("/") + color("N", "irrel") + color(")? ")))
            if i.strip().lower() in ['y', 'yes']:
                print color("marked relevant...", "rel")
                rel.add(doc)
                if rf: rf.write(doc.key + '\n')
            else:
                print color("marked irrelevant...", "irrel")
                irrel.add(doc)
                if irf: irf.write(doc.key + '\n')
    print ""

    l1, l2 = len(rel), len(irrel)
    p = float(l1) / (l1 + l2) if l1 > 0 else 0
    return rel, irrel, p


## main
def main(args):
    target_precision, query_terms, api, engine = validate(args)
    global nocol
    nocol = args.nocol

    # set Rocchio weights: relevant 0.75, irrelevant 0.25
    ro = Rocchio(0.75, 0.25)
    iteration, precision = 0, 0.0
    while iteration == 0 or precision < target_precision:
        print color("=" * 80, "delim")
        print color("[iteration: ", "bold") + color(str(iteration), "strong") + \
              color("]", "bold")
        print color("query: ", "bold") + color(" ".join(query_terms), "strong")
        # apply search on the current query terms
        docs = gsearch(" ".join(query_terms), api, engine)
        
        # collect user feedback
        rel, irrel, precision = feedback(docs, query_terms)
        print color("[iteration: ", "bold") + color(str(iteration), "strong") + color("] ", "bold") + \
              color(str(len(rel)), "strong") + color(" relevant, ", "bold") + \
              color(str(len(irrel)), "strong") + color(" irrelevant, ", "bold") + \
              color("%0.1f" % precision, "strong") + color(" precision", "bold")

        if precision >= target_precision:
            # target achieved
            print color("target precision %.1f has been achieved" % target_precision, "rel")
            break
        elif precision == 0:
            # no need to move on
            print color("no need to continue under zero precision", "error")
            break

        # update query string
        query_terms += ro.generate_query(rel, irrel, query_terms)

        iteration += 1
        if iteration >= 10:
            # maximum iteration
            print color("maximum iteration exceeded", "error")
            break

    print color("Exit...\n", "bold")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Relevance Feedback Demo')
    parser.add_argument('target_precision', type=float, help='target precision, (0, 1]')
    parser.add_argument('query', type=str, help='initial query string')
    parser.add_argument('--api', type=str, help='Google search API key')
    parser.add_argument('--engine', type=str, help='Google search engine ID')
    parser.add_argument('--nocol', action="store_true", help='Disable color prints')

    # args = vars()
    main(parser.parse_args())
