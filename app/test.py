from flask import render_template, flash, redirect, url_for, request
from initiator import app
import runspider
from forms import *
from SiteCrawler.spiders.myfuncs import *
import sqlite3
import datetime
import math
from operator import itemgetter

domain = "premierinn.com"
date = 1383305252

conn = sqlite3.connect(db_file)
c = conn.cursor()
scrapeid = select_from(c, "SELECT id FROM scrapes WHERE date = ?", date)[0][0]
urls = select_from(c, "SELECT url FROM nodes WHERE scrapeid = ?", scrapeid)
words = select_from(c, "SELECT url, word, freq FROM words WHERE scrapeid = ?", scrapeid)
sentences = select_from(c, "SELECT url, sentence FROM sentences WHERE scrapeid = ?", scrapeid)
url_word_count = select_from(c, "SELECT url, SUM(freq) FROM words WHERE scrapeid = ? GROUP BY url", scrapeid)
url_sentence_count = select_from(c, "SELECT url, COUNT(*) FROM sentences WHERE scrapeid = ? GROUP BY url", scrapeid)

print len(words)
print len(sentences)
	
sentences = [[url, sent, 1] for [url, sent] in sentences]

url_stats = {"Total":{"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}, "urls":{}}
w_group_size = 1
s_group_size = 5
longest_word = 1
longest_sent = 1

for [url] in urls:
	if url not in url_stats["urls"]:
		url_stats["urls"][url] = {"length":{"sent":{"labels":{}}, "word":{"labels":{}}}}

for url, word, freq in words:
	if real_word(word):
		length = len(word)
		if length > longest_word:
			longest_word = length

for url, sent, freq in sentences:
	length = sentence_length(sent)
	if length > longest_sent:
		longest_sent = length

def get_label_refs(longest, group_size):
	group_range = range(1, int(math.ceil(longest/float(group_size))+1))
	label_refs = {}
	for group_no in group_range:
		low_end = (int(group_no)-1)*group_size+1
		high_end = int(group_no)*group_size
		if low_end == high_end:
			label = "{0}".format(low_end)
		else:
			label = "{0} - {1}".format(low_end, high_end)
		label_refs[label] = range(low_end,high_end+1)
		labels = [label for label, lengths in sorted(label_refs.iteritems(), key=itemgetter(1))]
	return label_refs, labels
	
w_label_refs, w_labels = get_label_refs(longest_word, w_group_size)
s_label_refs, s_labels = get_label_refs(longest_sent, s_group_size)

def add_labels_lengths(label_refs, type, url):
	for label in label_refs:
		url_stats["urls"][url]["length"][type]["labels"][label] = {}
		for length in label_refs[label]:
			url_stats["urls"][url]["length"][type]["labels"][label][length] = {"freq":0, "items":[]}

for url in urls:
	add_labels_lengths(w_label_refs, "word", url[0])
	add_labels_lengths(s_label_refs, "sent", url[0])

for label in w_label_refs:
	url_stats["Total"]["length"]["word"]["labels"][label] = {}
	for length in w_label_refs[label]:
		url_stats["Total"]["length"]["word"]["labels"][label][length] = {"freq":0, "items":[]}
		
for label in s_label_refs:
	url_stats["Total"]["length"]["sent"]["labels"][label] = {}
	for length in s_label_refs[label]:
		url_stats["Total"]["length"]["sent"]["labels"][label][length] = {"freq":0, "items":[]}

def add_freqs_words(items_list, type, label_refs, length_func=None, validate_func=None):
	for url, item, freq in items_list:
		#print "{0}: {1} - {2}".format(url, item.encode("ascii", errors="ignore"), freq)
		# Remove this and put sentence filter in to remove "." further upstream
		if type == "sent" and len(item) <= 1:
			continue
		if validate_func:
			if not validate_func(item):
				continue
		
		if length_func:
			length = length_func(item)
		else:
			length = len(item)
		if length == 0:
			continue
		
		for lab, lengths in label_refs.iteritems():
			if length in lengths:
				label = lab
				continue
		
		#print "url: {0}, type: {1}, label: {2}, length: {3}, char_length: {4}, item: {5}".format(url, type, label, length, len(item), item.encode("ascii", errors="ignore"))
		url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"] += freq
		url_stats["urls"][url]["length"][type]["labels"][label][length]["items"].append(item)
		
		url_stats["Total"]["length"][type]["labels"][label][length]["freq"] += freq
		if item not in url_stats["Total"]["length"][type]["labels"][label][length]["items"]:
			url_stats["Total"]["length"][type]["labels"][label][length]["items"].append(item)

add_freqs_words(words, "word", w_label_refs, validate_func=real_word)
add_freqs_words(sentences, "sent", s_label_refs, length_func=sentence_length)

for type in ["word", "sent"]:

	for url in url_stats["urls"]:
		total = 0
		count = 0
		for label, lengths in url_stats["urls"][url]["length"][type]["labels"].iteritems():
			for length in lengths:
				freq = url_stats["urls"][url]["length"][type]["labels"][label][length]["freq"]
				total += length*freq
				count += freq
				#print "length: {0}, freq: {1}".format(length, freq)
		if count == 0:
			url_stats["urls"][url]["length"][type]["average"] = 0
		else:
			url_stats["urls"][url]["length"][type]["average"] = total/float(count)
	
	total = 0
	count = 0
	for label, lengths in url_stats["Total"]["length"][type]["labels"].iteritems():
		for length in lengths:
			freq = url_stats["Total"]["length"][type]["labels"][label][length]["freq"]
			total += length*freq
			count += freq
	if count == 0:
		url_stats["Total"]["length"][type]["average"] = 0
	else:
		url_stats["Total"]["length"][type]["average"] = total/float(count)


sentence_dump = [[sentence_length(sent), url, sent] for [url, sent, freq] in sentences if sentence_length(sent) >= 40]

#for url in url_stats["urls"]:
	#print "{0}: {1}".format(url, url_stats["urls"][url]["length"]["sent"]["average"])

conn.close()