from flask import render_template, flash, redirect, url_for, request
from initiator import app
import runspider
from forms import TextBox
from SiteCrawler.spiders.myfuncs import *
import sqlite3

# index view function suppressed for brevity

@app.route('/', methods = ['GET', 'POST'])
def start():
	form = TextBox()
	if form.validate_on_submit():
		if test_url(form.url.data):
			
			domain = get_domain(form.url.data)
			
			conn = sqlite3.connect('sitecrawler.db')
			c = conn.cursor()
			scrape_date = select_from(c, "SELECT date FROM scrapes WHERE domain = ? ORDER BY date DESC", domain)
			
			if scrape_date:
				return redirect(url_for('existing', route = form.url.data, date = scrape_date[0]))
			else:
				return redirect(url_for('runspider', route = form.url.data))
	return render_template('start.html', form = form)

@app.route('/existing/', methods = ['GET', 'POST'])
def existing():
	date = request.args.get('date')
	url_text = request.args.get('route')
	form = BoolForm()
	if form.validate_on_submit():
		if form.url.data == 1:
			return redirect(url_for('runspider', route = url_text))
		elif form.url.data == 0:
			return render_template('stop.html')
	return render_template('existing.html', form = form, date = date)