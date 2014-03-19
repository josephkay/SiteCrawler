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
from os import path as ospath
import shutil
import csv

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
	form.answer.choices = [("sitemap","Sitemap with screenshots"), ("social","Social media screenshots"), ("text","Text analysis"), ("content","Content analysis"), ("export","Export data")]
	if form.validate_on_submit():
		if form.answer.data == "sitemap":
			return redirect(url_for('sitemap', domain = domain, date = date))
		elif form.answer.data == "social":
			return redirect(url_for('social', domain = domain, date = date))
		elif form.answer.data == "text":
			return redirect(url_for('text', domain = domain, date = date))
		elif form.answer.data == "export":
			return redirect(url_for('export', domain = domain, date = date))
		elif form.answer.data == "content":
			return redirect(url_for('content', domain = domain, date = date))
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
		social_names = [name for [name] in social_names]
		for name in social_names:
			image_paths.append(r"/static/scrapes/{0}/{1}/{2}.png".format(domain, date, name))
	
	save_json(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), domain, date, "social_names"), social_names)  # MOVE THIS UP STREAM!
	
	conn.close()
	return render_template('social.html', image_paths = image_paths)

@app.route('/text/', methods = ['GET', 'POST'])
def text():
	domain = request.args.get('domain')
	date = request.args.get('date')
	
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	scrapeid = select_from(c, "SELECT id FROM scrapes WHERE date = ?", date)[0][0]
	text_data_list = select_from(c, "SELECT url, av_word_len, av_sent_len, word_count, sent_count FROM text_data WHERE scrapeid = ?", scrapeid)
	
	text_data_dict = {}
	
	for url, word_len, sent_len, word_count, sent_count in text_data_list:
		text_data_dict[url] = {}
		text_data_dict[url]["av_word_len"] = word_len
		text_data_dict[url]["av_sent_len"] = sent_len
		text_data_dict[url]["word_count"] = word_count
		text_data_dict[url]["sent_count"] = sent_count
	
	conn.close()
	
	save_json(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), domain, date, "text_data"), text_data_dict)  # MOVE THIS UP STREAM!
	
	folder_path_list = [item.encode("utf-8", errors="ignore") for item in ["scrapes", domain, date]]
	
	folder_path = "/".join(folder_path_list) + "/"
	
	extra_data_path = folder_path + "extra_data.json"
	
	return render_template('text.html', date = date, domain = domain, scrapeid = scrapeid, folder_path = folder_path, text_data = text_data_dict, extra_data_path = extra_data_path)

@app.route('/content/', methods = ['GET', 'POST'])
def content():
	domain = request.args.get('domain')
	date = request.args.get('date')
	
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	scrapeid = select_from(c, "SELECT id FROM scrapes WHERE date = ?", date)[0][0]
	content_data_list = select_from(c, "SELECT url, av_word_len, av_sent_len, word_count, sent_count FROM text_data WHERE scrapeid = ?", scrapeid)  # what will the format be?
	
	text_data_dict = {}
	
	for url, word_len, sent_len, word_count, sent_count in text_data_list:
		text_data_dict[url] = {}
		text_data_dict[url]["av_word_len"] = word_len
		text_data_dict[url]["av_sent_len"] = sent_len
		text_data_dict[url]["word_count"] = word_count
		text_data_dict[url]["sent_count"] = sent_count
	
	conn.close()
	
	save_json(r'{0}\initiator\static\scrapes\{1}\{2}\{3}.json'.format(getcwd(), domain, date, "text_data"), text_data_dict)  # MOVE THIS UP STREAM!
	
	folder_path_list = [item.encode("utf-8", errors="ignore") for item in ["scrapes", domain, date]]
	
	folder_path = "/".join(folder_path_list) + "/"
	
	extra_data_path = folder_path + "extra_data.json"
	
	return render_template('text.html', date = date, domain = domain, scrapeid = scrapeid, folder_path = folder_path, text_data = text_data_dict, extra_data_path = extra_data_path)

@app.route('/export/', methods = ['GET', 'POST'])
def export():
	domain = request.args.get('domain')
	date = request.args.get('date')
	
	root = getcwd()
	newfolder = r'{0}\{1}-{2}'.format(getcwd(),domain,date)
	newsubfolder = newfolder + r'\files'
	
	if ospath.exists(newfolder):
		message = "Export failed! Directory already Exists!"
		return render_template("export.html", message = message)
	else:
		shutil.copytree(r'{0}\initiator\static\scrapes\{1}\{2}'.format(root, domain, date), newsubfolder)
		shutil.copy(r'{0}\initiator\static\d3.js'.format(root), newsubfolder)
		shutil.copy(r'{0}\initiator\static\jquery.min.js'.format(root), newsubfolder)
		shutil.copy(r'{0}\initiator\static\Chart.js'.format(root), newsubfolder)
		shutil.copy(r'{0}\initiator\static\style.css'.format(root), newsubfolder)
		shutil.copy(r'{0}\initiator\export_templates\choose_graph.html'.format(root), newfolder)
		shutil.copy(r'{0}\initiator\export_templates\tree.html'.format(root), newsubfolder)
		shutil.copy(r'{0}\initiator\export_templates\text.html'.format(root), newsubfolder)
		shutil.copy(r'{0}\initiator\export_templates\social.html'.format(root), newsubfolder)
		
		
		conn = sqlite3.connect(db_file)
		c = conn.cursor()
		scrapeid = select_from(c, "SELECT id FROM scrapes WHERE date = ?", date)[0][0]
		text_data_list = select_from(c, "SELECT url, av_word_len, av_sent_len, word_count, sent_count FROM text_data WHERE scrapeid = ?", scrapeid)
		
		conn.close()
		
		csv_text_file = open(r'{0}\{1}'.format(newfolder, "text_data.csv"), "wb")
		csv_text = csv.writer(csv_text_file, delimiter=",")
		csv_text.writerow(["url","Average word length","Average sentence length","Word count","Sentence count"])
		
		for row in text_data_list:
			csv_text.writerow(list(row))
		
		csv_text_file.close()
		
		
		json_data = open(r'{0}\initiator\static\scrapes\{1}\{2}\sitemap.json'.format(root, domain, date))
		sitemap = [json.load(json_data)]
		
		depth = 0
		
		csv_sitemap_file = open(r'{0}\{1}'.format(newfolder, "sitemap.csv"), "wb")
		csv_sitemap = csv.writer(csv_sitemap_file, delimiter=",")
		
		make_csv_sitemap(csv_sitemap, sitemap, depth)
		
		csv_sitemap_file.close()
		
		message = "Export successful!"
		return render_template("export.html", message = message)