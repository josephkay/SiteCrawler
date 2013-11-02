from flask import render_template, flash, redirect, url_for, request
from initiator import app
import runspider
from forms import *
from SiteCrawler.spiders.myfuncs import *
import sqlite3
import datetime
import math
from operator import itemgetter
import json
from os import getcwd

@app.route('/', methods = ['GET', 'POST'])
def start():
	form = TextBox()
	if form.validate_on_submit():
		if test_url(form.url.data):
			
			domain = get_domain(form.url.data)
			
			conn = sqlite3.connect(db_file)
			c = conn.cursor()
			scrape_date = select_from(c, "SELECT date FROM scrapes WHERE domain = ? ORDER BY date DESC", domain)
			
			if scrape_date:
				return redirect(url_for('existing', route = form.url.data, domain = domain))
			else:
				return redirect(url_for('runspider', route = form.url.data, domain = domain))
	return render_template('start.html', form = form)

@app.route('/existing/', methods = ['GET', 'POST'])
def existing():
	url_text = request.args.get('route')
	domain = request.args.get('domain')
	form = RadioForm()
	form.answer.choices = [("scrape","Scrape again"), ("results","View existing results")]
	if form.validate_on_submit():
		if form.answer.data == "scrape":
			return redirect(url_for('runspider', route = url_text, domain = domain))
		elif form.answer.data == "results":
			return redirect(url_for('results', domain = domain))
		else:
			return redirect(url_for('existing', route = url_text, domain = domain))
	return render_template('existing.html', form = form)

@app.route('/stop/', methods = ['GET', 'POST'])
def stop():
	return render_template('stop.html')

@app.route('/results/', methods = ['GET', 'POST'])
def results():
	domain = request.args.get('domain')
	
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	scrape_date = select_from(c, "SELECT date FROM scrapes WHERE domain = ? ORDER BY date DESC", domain)
	
	form = RadioForm()
	choice_list = []
	for [date] in scrape_date:
		choice_list.append((str(date), datetime.datetime.utcfromtimestamp(date)))
	form.answer.choices = choice_list
	if form.validate_on_submit():
		return redirect(url_for('choose_graph', domain = domain, date = form.answer.data))
		
	conn.close()
	return render_template('results.html', form = form)

@app.route('/choose_graph/', methods = ['GET', 'POST'])
def choose_graph():
	domain = request.args.get('domain')
	date = request.args.get('date')
	form = RadioForm()
	form.answer.choices = [("sitemap","Sitemap with screenshots"), ("social","Social media screenshots"), ("text","Text analysis")]
	if form.validate_on_submit():
		if form.answer.data == "sitemap":
			return redirect(url_for('sitemap', domain = domain, date = date))
		elif form.answer.data == "social":
			return redirect(url_for('social', domain = domain, date = date))
		elif form.answer.data == "text":
			return redirect(url_for('text', domain = domain, date = date))
		else:
			return redirect(url_for('choose_graph', domain = domain, date = date))
	return render_template('choose_graph.html', form = form)

@app.route('/sitemap/', methods = ['GET', 'POST'])
def sitemap():
	domain = request.args.get('domain')
	date = request.args.get('date')
	json_data = r"scrapes/{0}/{1}/sitemap.json".format(domain, date)
	image_path = r"/static/scrapes/{0}/{1}/".format(domain, date)
	return render_template('tree.html', json_data = json_data, image_path = image_path, domain = domain)

@app.route('/screenshot/', methods = ['GET', 'POST'])
def screenshot():
	image_path = request.args.get('image_path')
	return render_template('screenshot.html', image_path = image_path)

@app.route('/social/', methods = ['GET', 'POST'])
def social():
	domain = request.args.get('domain')
	date = request.args.get('date')
	
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	scrapeid = select_from(c, "SELECT id FROM scrapes WHERE date = ?", date)[0][0]
	social_names = select_from(c, "SELECT name FROM nodes WHERE social = 1 AND scrapeid = ?", scrapeid)
	
	image_paths = []
	if social_names:
		for name in social_names:
			image_paths.append(r"/static/scrapes/{0}/{1}/{2}.png".format(domain, date, name[0]))
	
	conn.close()
	return render_template('social.html', image_paths = image_paths)

@app.route('/text/', methods = ['GET', 'POST'])
def text():
	domain = request.args.get('domain')
	date = request.args.get('date')
	
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	scrapeid = select_from(c, "SELECT id FROM scrapes WHERE date = ?", date)[0][0]
	urls = select_from(c, "SELECT url FROM nodes WHERE scrapeid = ?", scrapeid)
	words = select_from(c, "SELECT url, word, freq FROM words WHERE scrapeid = ?", scrapeid)
	sentences = select_from(c, "SELECT url, sentence FROM sentences WHERE scrapeid = ?", scrapeid)
	url_word_count = select_from(c, "SELECT url, SUM(freq) FROM words WHERE scrapeid = ? GROUP BY url", scrapeid)
	url_sentence_count = select_from(c, "SELECT url, COUNT(*) FROM sentences WHERE scrapeid = ? GROUP BY url", scrapeid)
		
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
	
	name_url_dict = {}
	long_count = 0
	
	for url in url_stats["urls"]:
		name = url.replace("/", "-")
		for char in [":","<",">","?","\"","*","."]:
			name = name.replace(char, "")
		if len(name) > 100:
			name = name[:80] + "---#" + str(long_count)
			long_count += 1
		with open(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), domain, date, name), 'w') as outfile:
			json.dump(url_stats["urls"][url], outfile)
		name_url_dict[name] = url

	conn.close()
	return render_template('text.html', name_url_dict = name_url_dict, w_labels = w_labels, s_labels = s_labels)