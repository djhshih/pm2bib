#!/usr/bin/env python3

# Author:  David JH Shih <djh.shih@gmail.com>
# License: GPLv3
# Date:    2012-04-14
# Version: 0.1

import os, argparse, os.path, re
import urllib.request as request, urllib.parse as parse


def medline2bib(medline):

	def prefix_strip(line):
		return line[6:]

	def get_year(date):
		i = date.find(' ')
		if i != -1:
			return date[:i]
		return date

	def lastdot_strip(s):
		if s:
			if s.endswith('.'):
				s = s[:len(s)-1]
		return s

	def lastand_strip(s):
		if s:
			if s.endswith(' and '):
				s = s[:len(s)-5]
		return s

	# Itemize lines

	# split lines into items, to account for multiline items
	items = []
	item = ''
	for line in medline.split('\n'):
		if line:
			if line[0] != ' ':
				# first character is not a space: start a new item
				items.append(item)
				item = line
			else:
				# the current line is a continuation of the last item
				item += ' ' + line.lstrip()
	
	# remove the first item, which is empty
	items = items[1:]

	# Populate dictionary

	fields = {}
	fields['author'] = ''
	for item in items:
		if item[:4] == 'PMID':
			fields['pmid'] = prefix_strip(item)
		elif item[:2] == 'VI':
			fields['volume'] = prefix_strip(item)
		elif item[:2] == 'IP':
			fields['number'] = prefix_strip(item)
		elif item[:2] == 'DP':
			fields['year'] = get_year( prefix_strip(item) )
		elif item[:2] == 'TI':
			fields['title'] = '{' + lastdot_strip( prefix_strip(item) ) + '}'
		elif item[:2] == 'PG':
			fields['pages'] = prefix_strip(item).replace('-', '--')
		elif item[:2] == 'TA':
			fields['journal'] = '{' + prefix_strip(item) + '}'
		elif item[:3] == 'AID':
			# N.B. not always the DOI
			fields['doi'] = prefix_strip(item)
		elif item[:3] == 'FAU':
			fields['author'] += '{} and '.format(prefix_strip(item))
	# strip off last 'and'
	fields['author'] = lastand_strip(fields['author'])

	# assuming each author is in (surname, given names) format
	# derive the key from the surname of the last author and last two digits of the year
	author = fields['author']
	year = fields['year']
	key = '{}{}'.format( author[:author.find(',')].lower().replace(' ', ''), year[2:] )

	# Construct Bibtex entry

	result = '@article{%s,\n' % key	
	for k, v in fields.items():
		result += '\t{} = "{}",\n'.format(k, v)
	result += '}\n'

	return result


def query_pubmed(url, query):

	params = parse.urlencode( {'term': query, 'report': 'medline'} )
	base_url = '{}?%s'.format(url)
	f = request.urlopen(base_url % params)
	data = f.read().decode('utf-8')

	# Clean-up data string

	# use only substring within pre tags
	open_tag, close_tag = '<pre>', '</pre>'
	start, end = data.find(open_tag), data.find(close_tag)
	# check that the result is not empty
	if start != -1 and end != -1:
		# displace start by len of open tag plus 1 (to remove \n)
		data = data[ start+len(open_tag)+1 : end ]

	# split data into individual entries
	# entries by delimited by a blank line
	medlines = data.split('\n\n')

	results = ''
	for medline in medlines:
		results += medline2bib(medline)

	return results

def main():

	pr = argparse.ArgumentParser(description='Converts pubmed ID to Bibtex reference')
	pr.add_argument('query', help='Pubmed query, default: Pubmed accession number (PMID)')
	pr.add_argument('-f', '--file', dest='file', action='store_const', const=True, default=False, help='query is an input text file of queries')
	pr.add_argument('--url', help='Pubmed URL', default='http://www.ncbi.nlm.nih.gov/pubmed')

	argv = pr.parse_args()

	if argv.file:
		results = ''
		with open(argv.query, 'r') as inf:
			for line in inf:
				results += query_pubmed(argv.url, line.strip())
	else:
		results = query_pubmed(argv.url, argv.query)

	print(results)


if __name__ == '__main__':
	main()

