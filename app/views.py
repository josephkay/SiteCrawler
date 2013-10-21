from flask import render_template, flash, redirect, url_for, request
from initiator import app
import runspider
from forms import *
from SiteCrawler.spiders.myfuncs import *
import sqlite3
import datetime

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
	url_stats = {}
	word_len_freqs = {}
	sent_len_freqs = {}
	
	for url, word, freq in words:
		length = len(word)
		if url not in url_stats:
			url_stats[url] = [length*freq, freq, 0, 1]
		else:
			url_stats[url][1] += freq
			url_stats[url][0] += length*freq
	
	for url, sentence in sentences:
		length = sentence_length(sentence)
		if url not in url_stats:
			url_stats[url] = [0, 1, length, 1]
		else:
			if url_stats[url][2] != 0:
				url_stats[url][3] += 1
			url_stats[url][2] += length
	
	url_stats = [[url, stats[0]/stats[1], stats[2]/stats[3]] for [url, stats] in url_stats.iteritems()]
	
	for length, freq in [[len(word), freq] for word, freq, url in words]:
		if length not in word_len_freqs:
			word_len_freqs[length] = freq
		else:
			word_len_freqs[length] += freq
	
	for sentence, url in sentences:
		length = sentence_length(sentence)
		if length not in sent_len_freqs:
			sent_len_freqs[length] = 1
		else:
			sent_len_freqs[length] += 1
	
	conn.close()
	return render_template('text.html', url_stats = url_stats, word_len_freqs = word_len_freqs, sent_len_freqs = sent_len_freqs, sentences = [[sentence_length(sent), url, sent] for [url, sent] in sentences if sentence_length(sent) >= 40])